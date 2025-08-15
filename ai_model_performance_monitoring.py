"""
AI Model Performance Monitoring System
Real-time monitoring, alerting, and performance analytics for deployed AI models
"""

import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import pandas as pd
import numpy as np
import redis.asyncio as redis
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor
import sqlite3
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# Medical schema integration
from comprehensive_medical_schema import ComprehensiveMedicalSchema, MedicalValidationEngine

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of metrics to monitor"""
    ACCURACY = "accuracy"
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    GPU_USAGE = "gpu_usage"
    INFERENCE_TIME = "inference_time"
    QUEUE_LENGTH = "queue_length"
    MEDICAL_ACCURACY = "medical_accuracy"
    HIPAA_COMPLIANCE = "hipaa_compliance"
    DATA_DRIFT = "data_drift"
    MODEL_DRIFT = "model_drift"
    FAIRNESS_SCORE = "fairness_score"
    BIAS_DETECTION = "bias_detection"

class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertStatus(Enum):
    """Alert status"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    MUTED = "muted"

@dataclass
class MetricDefinition:
    """Definition of a metric to monitor"""
    name: str
    metric_type: MetricType
    description: str
    aggregation_function: str  # mean, max, min, p95, p99
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    window_size_minutes: int = 5
    medical_critical: bool = False
    enabled: bool = True

@dataclass
class MetricValue:
    """A single metric measurement"""
    timestamp: datetime
    model_id: str
    metric_name: str
    value: float
    dimensions: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    user_id: Optional[str] = None

@dataclass
class Alert:
    """Performance alert"""
    id: str
    model_id: str
    metric_name: str
    severity: AlertSeverity
    status: AlertStatus
    message: str
    threshold: float
    current_value: float
    triggered_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    context: Dict[str, Any] = field(default_factory=dict)

class ModelPerformanceMonitor:
    """Comprehensive model performance monitoring system"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", db_path: str = "monitoring.db"):
        self.redis_url = redis_url
        self.db_path = db_path
        self.redis_client = None
        self.db_connection = None
        
        # Metric storage
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.aggregated_metrics: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.metric_definitions: Dict[str, MetricDefinition] = {}
        self.alerts: Dict[str, Alert] = {}
        
        # Monitoring configuration
        self.monitoring_interval = 30  # seconds
        self.retention_days = 30
        self.max_metrics_in_memory = 10000
        
        # Background workers
        self.monitoring_active = False
        self.aggregation_active = False
        self.cleanup_active = False
        
        # Medical schema integration
        self.medical_schema = None
        self.medical_validator = None
        
        # Alert handlers
        self.alert_handlers: List[Callable] = []
        
        # Initialize default metrics
        self._initialize_default_metrics()
    
    async def initialize(self):
        """Initialize the monitoring system"""
        try:
            # Initialize Redis connection
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            
            # Initialize SQLite database
            self._initialize_database()
            
            # Initialize medical schema if available
            try:
                self.medical_schema = ComprehensiveMedicalSchema()
                await self.medical_schema.initialize()
                
                self.medical_validator = MedicalValidationEngine()
                await self.medical_validator.initialize()
            except Exception as e:
                logger.warning(f"Medical schema not available: {e}")
            
            # Start background workers
            self._start_background_workers()
            
            logger.info("Model Performance Monitor initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Model Performance Monitor: {e}")
            raise e
    
    def _initialize_database(self):
        """Initialize SQLite database for persistent storage"""
        self.db_connection = sqlite3.connect(self.db_path, check_same_thread=False)
        
        # Create tables
        cursor = self.db_connection.cursor()
        
        # Metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                model_id TEXT,
                metric_name TEXT,
                value REAL,
                dimensions TEXT,
                session_id TEXT,
                user_id TEXT
            )
        ''')
        
        # Alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id TEXT PRIMARY KEY,
                model_id TEXT,
                metric_name TEXT,
                severity TEXT,
                status TEXT,
                message TEXT,
                threshold REAL,
                current_value REAL,
                triggered_at TEXT,
                acknowledged_at TEXT,
                resolved_at TEXT,
                context TEXT
            )
        ''')
        
        # Performance summary table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id TEXT,
                date TEXT,
                avg_accuracy REAL,
                avg_latency REAL,
                total_requests INTEGER,
                error_count INTEGER,
                uptime_percentage REAL
            )
        ''')
        
        # Medical metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS medical_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                model_id TEXT,
                medical_accuracy REAL,
                hipaa_compliance_score REAL,
                terminology_accuracy REAL,
                clinical_relevance REAL,
                safety_score REAL
            )
        ''')
        
        self.db_connection.commit()
    
    def _initialize_default_metrics(self):
        """Initialize default metric definitions"""
        default_metrics = [
            MetricDefinition(
                name="accuracy",
                metric_type=MetricType.ACCURACY,
                description="Model prediction accuracy",
                aggregation_function="mean",
                threshold_warning=0.85,
                threshold_critical=0.80,
                window_size_minutes=5
            ),
            MetricDefinition(
                name="latency",
                metric_type=MetricType.LATENCY,
                description="Model inference latency (ms)",
                aggregation_function="p95",
                threshold_warning=1000.0,
                threshold_critical=2000.0,
                window_size_minutes=5
            ),
            MetricDefinition(
                name="error_rate",
                metric_type=MetricType.ERROR_RATE,
                description="Error rate percentage",
                aggregation_function="mean",
                threshold_warning=5.0,
                threshold_critical=10.0,
                window_size_minutes=5
            ),
            MetricDefinition(
                name="memory_usage",
                metric_type=MetricType.MEMORY_USAGE,
                description="Memory usage percentage",
                aggregation_function="mean",
                threshold_warning=80.0,
                threshold_critical=90.0,
                window_size_minutes=5
            ),
            MetricDefinition(
                name="cpu_usage",
                metric_type=MetricType.CPU_USAGE,
                description="CPU usage percentage",
                aggregation_function="mean",
                threshold_warning=80.0,
                threshold_critical=90.0,
                window_size_minutes=5
            ),
            MetricDefinition(
                name="medical_accuracy",
                metric_type=MetricType.MEDICAL_ACCURACY,
                description="Medical terminology accuracy",
                aggregation_function="mean",
                threshold_warning=0.90,
                threshold_critical=0.85,
                window_size_minutes=5,
                medical_critical=True
            ),
            MetricDefinition(
                name="hipaa_compliance",
                metric_type=MetricType.HIPAA_COMPLIANCE,
                description="HIPAA compliance score",
                aggregation_function="min",
                threshold_warning=0.95,
                threshold_critical=0.90,
                window_size_minutes=5,
                medical_critical=True
            )
        ]
        
        for metric in default_metrics:
            self.metric_definitions[metric.name] = metric
    
    def _start_background_workers(self):
        """Start background monitoring workers"""
        self.monitoring_active = True
        self.aggregation_active = True
        self.cleanup_active = True
        
        # Metrics collection worker
        threading.Thread(target=self._metrics_collection_worker, daemon=True).start()
        
        # Aggregation worker
        threading.Thread(target=self._aggregation_worker, daemon=True).start()
        
        # Alert checking worker
        threading.Thread(target=self._alert_checking_worker, daemon=True).start()
        
        # Cleanup worker
        threading.Thread(target=self._cleanup_worker, daemon=True).start()
    
    def _metrics_collection_worker(self):
        """Background worker for collecting system metrics"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                system_metrics = self._collect_system_metrics()
                
                for metric_name, value in system_metrics.items():
                    self.record_metric(
                        model_id="system",
                        metric_name=metric_name,
                        value=value
                    )
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                time.sleep(30)
    
    def _aggregation_worker(self):
        """Background worker for aggregating metrics"""
        while self.aggregation_active:
            try:
                # Aggregate metrics for all models
                for model_id in set(metric.model_id for metrics_list in self.metrics.values() for metric in metrics_list):
                    if model_id != "system":
                        self._aggregate_model_metrics(model_id)
                
                time.sleep(60)  # Run every minute
                
            except Exception as e:
                logger.error(f"Aggregation worker error: {e}")
                time.sleep(60)
    
    def _alert_checking_worker(self):
        """Background worker for checking alert conditions"""
        while self.monitoring_active:
            try:
                self._check_alert_conditions()
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Alert checking error: {e}")
                time.sleep(30)
    
    def _cleanup_worker(self):
        """Background worker for cleaning up old data"""
        while self.cleanup_active:
            try:
                self._cleanup_old_data()
                time.sleep(3600)  # Run every hour
                
            except Exception as e:
                logger.error(f"Cleanup worker error: {e}")
                time.sleep(3600)
    
    def _collect_system_metrics(self) -> Dict[str, float]:
        """Collect system-level metrics"""
        try:
            return {
                "cpu_usage": psutil.cpu_percent(interval=1),
                "memory_usage": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent,
                "gpu_memory": self._get_gpu_memory_usage()
            }
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {}
    
    def _get_gpu_memory_usage(self) -> float:
        """Get GPU memory usage if available"""
        try:
            import torch
            if torch.cuda.is_available():
                return torch.cuda.memory_allocated() / torch.cuda.max_memory_allocated() * 100
        except:
            pass
        return 0.0
    
    def record_metric(
        self,
        model_id: str,
        metric_name: str,
        value: float,
        dimensions: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """Record a metric value"""
        metric = MetricValue(
            timestamp=datetime.now(),
            model_id=model_id,
            metric_name=metric_name,
            value=value,
            dimensions=dimensions or {},
            session_id=session_id,
            user_id=user_id
        )
        
        # Store in memory
        key = f"{model_id}:{metric_name}"
        self.metrics[key].append(metric)
        
        # Store in Redis for real-time access
        if self.redis_client:
            asyncio.create_task(self._store_metric_in_redis(metric))
        
        # Store in database
        self._store_metric_in_database(metric)
    
    async def _store_metric_in_redis(self, metric: MetricValue):
        """Store metric in Redis with TTL"""
        try:
            key = f"metric:{metric.model_id}:{metric.metric_name}"
            value = {
                "timestamp": metric.timestamp.isoformat(),
                "value": metric.value,
                "dimensions": metric.dimensions
            }
            
            # Store with 1 hour TTL
            await self.redis_client.setex(key, 3600, json.dumps(value))
            
            # Add to time series
            ts_key = f"ts:{metric.model_id}:{metric.metric_name}"
            await self.redis_client.zadd(
                ts_key,
                {json.dumps(value): metric.timestamp.timestamp()}
            )
            
            # Keep only last 1000 entries
            await self.redis_client.zremrangebyrank(ts_key, 0, -1001)
            
        except Exception as e:
            logger.error(f"Error storing metric in Redis: {e}")
    
    def _store_metric_in_database(self, metric: MetricValue):
        """Store metric in database"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                INSERT INTO metrics (
                    timestamp, model_id, metric_name, value, 
                    dimensions, session_id, user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                metric.timestamp.isoformat(),
                metric.model_id,
                metric.metric_name,
                metric.value,
                json.dumps(metric.dimensions),
                metric.session_id,
                metric.user_id
            ))
            self.db_connection.commit()
            
        except Exception as e:
            logger.error(f"Error storing metric in database: {e}")
    
    def _aggregate_model_metrics(self, model_id: str):
        """Aggregate metrics for a specific model"""
        now = datetime.now()
        
        for metric_name, definition in self.metric_definitions.items():
            if not definition.enabled:
                continue
            
            # Get metrics from the specified window
            window_start = now - timedelta(minutes=definition.window_size_minutes)
            key = f"{model_id}:{metric_name}"
            
            if key not in self.metrics:
                continue
            
            # Filter metrics by time window
            window_metrics = [
                m for m in self.metrics[key]
                if m.timestamp >= window_start
            ]
            
            if not window_metrics:
                continue
            
            # Calculate aggregated value
            values = [m.value for m in window_metrics]
            
            if definition.aggregation_function == "mean":
                aggregated_value = np.mean(values)
            elif definition.aggregation_function == "max":
                aggregated_value = np.max(values)
            elif definition.aggregation_function == "min":
                aggregated_value = np.min(values)
            elif definition.aggregation_function == "p95":
                aggregated_value = np.percentile(values, 95)
            elif definition.aggregation_function == "p99":
                aggregated_value = np.percentile(values, 99)
            else:
                aggregated_value = np.mean(values)
            
            # Store aggregated value
            self.aggregated_metrics[model_id][metric_name] = {
                "value": aggregated_value,
                "timestamp": now.isoformat(),
                "count": len(values),
                "raw_values": values[-10:]  # Keep last 10 raw values
            }
    
    def _check_alert_conditions(self):
        """Check for alert conditions across all models and metrics"""
        for model_id, metrics in self.aggregated_metrics.items():
            for metric_name, data in metrics.items():
                definition = self.metric_definitions.get(metric_name)
                if not definition:
                    continue
                
                current_value = data["value"]
                
                # Check critical threshold
                if definition.threshold_critical is not None:
                    if (definition.metric_type in [MetricType.ACCURACY, MetricType.MEDICAL_ACCURACY, MetricType.HIPAA_COMPLIANCE] and 
                        current_value < definition.threshold_critical) or \
                       (definition.metric_type not in [MetricType.ACCURACY, MetricType.MEDICAL_ACCURACY, MetricType.HIPAA_COMPLIANCE] and 
                        current_value > definition.threshold_critical):
                        self._trigger_alert(
                            model_id,
                            metric_name,
                            AlertSeverity.CRITICAL,
                            current_value,
                            definition.threshold_critical,
                            definition
                        )
                
                # Check warning threshold
                elif definition.threshold_warning is not None:
                    if (definition.metric_type in [MetricType.ACCURACY, MetricType.MEDICAL_ACCURACY, MetricType.HIPAA_COMPLIANCE] and 
                        current_value < definition.threshold_warning) or \
                       (definition.metric_type not in [MetricType.ACCURACY, MetricType.MEDICAL_ACCURACY, MetricType.HIPAA_COMPLIANCE] and 
                        current_value > definition.threshold_warning):
                        self._trigger_alert(
                            model_id,
                            metric_name,
                            AlertSeverity.HIGH if definition.medical_critical else AlertSeverity.MEDIUM,
                            current_value,
                            definition.threshold_warning,
                            definition
                        )
    
    def _trigger_alert(
        self,
        model_id: str,
        metric_name: str,
        severity: AlertSeverity,
        current_value: float,
        threshold: float,
        definition: MetricDefinition
    ):
        """Trigger an alert"""
        alert_id = f"{model_id}:{metric_name}:{severity.value}"
        
        # Check if alert already exists and is active
        if alert_id in self.alerts and self.alerts[alert_id].status == AlertStatus.ACTIVE:
            return
        
        # Create alert
        alert = Alert(
            id=alert_id,
            model_id=model_id,
            metric_name=metric_name,
            severity=severity,
            status=AlertStatus.ACTIVE,
            message=f"{definition.description} {metric_name} threshold exceeded: {current_value:.3f} (threshold: {threshold:.3f})",
            threshold=threshold,
            current_value=current_value,
            triggered_at=datetime.now(),
            context={
                "metric_type": definition.metric_type.value,
                "medical_critical": definition.medical_critical,
                "aggregation_function": definition.aggregation_function
            }
        )
        
        self.alerts[alert_id] = alert
        
        # Store in database
        self._store_alert_in_database(alert)
        
        # Notify alert handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler error: {e}")
        
        logger.warning(f"Alert triggered: {alert.message}")
    
    def _store_alert_in_database(self, alert: Alert):
        """Store alert in database"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO alerts (
                    id, model_id, metric_name, severity, status, message,
                    threshold, current_value, triggered_at, acknowledged_at,
                    resolved_at, context
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert.id,
                alert.model_id,
                alert.metric_name,
                alert.severity.value,
                alert.status.value,
                alert.message,
                alert.threshold,
                alert.current_value,
                alert.triggered_at.isoformat(),
                alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                alert.resolved_at.isoformat() if alert.resolved_at else None,
                json.dumps(alert.context)
            ))
            self.db_connection.commit()
            
        except Exception as e:
            logger.error(f"Error storing alert in database: {e}")
    
    def _cleanup_old_data(self):
        """Clean up old metrics and alerts"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        try:
            cursor = self.db_connection.cursor()
            
            # Clean up old metrics
            cursor.execute(
                "DELETE FROM metrics WHERE timestamp < ?",
                (cutoff_date.isoformat(),)
            )
            
            # Clean up resolved alerts older than 7 days
            alert_cutoff = datetime.now() - timedelta(days=7)
            cursor.execute(
                "DELETE FROM alerts WHERE status = 'resolved' AND resolved_at < ?",
                (alert_cutoff.isoformat(),)
            )
            
            self.db_connection.commit()
            
            logger.info(f"Cleaned up data older than {self.retention_days} days")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def get_model_metrics(
        self,
        model_id: str,
        metric_names: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get metrics for a specific model"""
        if start_time is None:
            start_time = datetime.now() - timedelta(hours=24)
        if end_time is None:
            end_time = datetime.now()
        
        cursor = self.db_connection.cursor()
        
        # Build query
        query = '''
            SELECT metric_name, timestamp, value, dimensions
            FROM metrics
            WHERE model_id = ? AND timestamp BETWEEN ? AND ?
        '''
        params = [model_id, start_time.isoformat(), end_time.isoformat()]
        
        if metric_names:
            placeholders = ','.join(['?' for _ in metric_names])
            query += f' AND metric_name IN ({placeholders})'
            params.extend(metric_names)
        
        query += ' ORDER BY timestamp DESC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Group by metric name
        result = defaultdict(list)
        for row in rows:
            metric_name, timestamp, value, dimensions_json = row
            result[metric_name].append({
                "timestamp": timestamp,
                "value": value,
                "dimensions": json.loads(dimensions_json) if dimensions_json else {}
            })
        
        return dict(result)
    
    def get_current_metrics(self, model_id: str) -> Dict[str, Any]:
        """Get current aggregated metrics for a model"""
        return self.aggregated_metrics.get(model_id, {})
    
    def get_active_alerts(self, model_id: Optional[str] = None) -> List[Alert]:
        """Get active alerts"""
        active_alerts = [
            alert for alert in self.alerts.values()
            if alert.status == AlertStatus.ACTIVE
        ]
        
        if model_id:
            active_alerts = [
                alert for alert in active_alerts
                if alert.model_id == model_id
            ]
        
        return sorted(active_alerts, key=lambda x: x.triggered_at, reverse=True)
    
    def acknowledge_alert(self, alert_id: str, user_id: str):
        """Acknowledge an alert"""
        if alert_id in self.alerts:
            self.alerts[alert_id].status = AlertStatus.ACKNOWLEDGED
            self.alerts[alert_id].acknowledged_at = datetime.now()
            self._store_alert_in_database(self.alerts[alert_id])
            logger.info(f"Alert {alert_id} acknowledged by {user_id}")
    
    def resolve_alert(self, alert_id: str, user_id: str):
        """Resolve an alert"""
        if alert_id in self.alerts:
            self.alerts[alert_id].status = AlertStatus.RESOLVED
            self.alerts[alert_id].resolved_at = datetime.now()
            self._store_alert_in_database(self.alerts[alert_id])
            logger.info(f"Alert {alert_id} resolved by {user_id}")
    
    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """Add an alert handler function"""
        self.alert_handlers.append(handler)
    
    def create_performance_dashboard(self, model_id: str) -> Dict[str, Any]:
        """Create performance dashboard data for a model"""
        # Get metrics for the last 24 hours
        metrics = self.get_model_metrics(model_id)
        current_metrics = self.get_current_metrics(model_id)
        active_alerts = self.get_active_alerts(model_id)
        
        # Create visualizations
        charts = []
        
        # Accuracy over time
        if "accuracy" in metrics:
            accuracy_data = metrics["accuracy"]
            fig_accuracy = go.Figure()
            fig_accuracy.add_trace(go.Scatter(
                x=[data["timestamp"] for data in accuracy_data],
                y=[data["value"] for data in accuracy_data],
                mode='lines+markers',
                name='Accuracy',
                line=dict(color='blue')
            ))
            fig_accuracy.update_layout(
                title="Model Accuracy Over Time",
                xaxis_title="Time",
                yaxis_title="Accuracy",
                height=400
            )
            charts.append({"name": "accuracy", "chart": fig_accuracy.to_json()})
        
        # Latency distribution
        if "latency" in metrics:
            latency_data = [data["value"] for data in metrics["latency"]]
            fig_latency = go.Figure()
            fig_latency.add_trace(go.Histogram(
                x=latency_data,
                nbinsx=50,
                name='Latency Distribution',
                marker_color='green'
            ))
            fig_latency.update_layout(
                title="Latency Distribution",
                xaxis_title="Latency (ms)",
                yaxis_title="Frequency",
                height=400
            )
            charts.append({"name": "latency", "chart": fig_latency.to_json()})
        
        # System metrics
        system_metrics = ["cpu_usage", "memory_usage"]
        system_data = {}
        for metric in system_metrics:
            if metric in metrics:
                system_data[metric] = [data["value"] for data in metrics[metric][-100:]]
        
        if system_data:
            fig_system = make_subplots(
                rows=len(system_data), cols=1,
                subplot_titles=list(system_data.keys()),
                vertical_spacing=0.1
            )
            
            for i, (metric, values) in enumerate(system_data.items(), 1):
                fig_system.add_trace(
                    go.Scatter(
                        y=values,
                        mode='lines',
                        name=metric,
                        line=dict(color='red' if i == 1 else 'orange')
                    ),
                    row=i, col=1
                )
            
            fig_system.update_layout(
                title="System Resource Usage",
                height=400 * len(system_data),
                showlegend=False
            )
            charts.append({"name": "system", "chart": fig_system.to_json()})
        
        return {
            "model_id": model_id,
            "current_metrics": current_metrics,
            "active_alerts": [
                {
                    "id": alert.id,
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "triggered_at": alert.triggered_at.isoformat()
                }
                for alert in active_alerts
            ],
            "charts": charts,
            "summary": {
                "total_requests": len(metrics.get("accuracy", [])),
                "avg_accuracy": np.mean([data["value"] for data in metrics.get("accuracy", [])]) if "accuracy" in metrics else None,
                "avg_latency": np.mean([data["value"] for data in metrics.get("latency", [])]) if "latency" in metrics else None,
                "error_rate": current_metrics.get("error_rate", {}).get("value", 0)
            }
        }
    
    async def record_medical_metrics(
        self,
        model_id: str,
        prediction: str,
        actual: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """Record medical-specific metrics"""
        if not self.medical_validator:
            return
        
        try:
            # Validate medical content
            validation_result = await self.medical_validator.validate_content(prediction)
            
            # Record medical accuracy
            if actual:
                medical_accuracy = await self.medical_validator.calculate_medical_accuracy(prediction, actual)
                self.record_metric(model_id, "medical_accuracy", medical_accuracy, session_id=session_id)
            
            # Record HIPAA compliance
            hipaa_score = validation_result.get("hipaa_compliance_score", 1.0)
            self.record_metric(model_id, "hipaa_compliance", hipaa_score, session_id=session_id)
            
            # Record terminology accuracy
            terminology_accuracy = validation_result.get("terminology_accuracy", 1.0)
            self.record_metric(model_id, "terminology_accuracy", terminology_accuracy, session_id=session_id)
            
            # Store in medical metrics table
            cursor = self.db_connection.cursor()
            cursor.execute('''
                INSERT INTO medical_metrics (
                    timestamp, model_id, medical_accuracy, hipaa_compliance_score,
                    terminology_accuracy, clinical_relevance, safety_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                model_id,
                validation_result.get("medical_accuracy", 0.0),
                hipaa_score,
                terminology_accuracy,
                validation_result.get("clinical_relevance", 0.0),
                validation_result.get("safety_score", 0.0)
            ))
            self.db_connection.commit()
            
        except Exception as e:
            logger.error(f"Error recording medical metrics: {e}")
    
    def shutdown(self):
        """Shutdown the monitoring system"""
        self.monitoring_active = False
        self.aggregation_active = False
        self.cleanup_active = False
        
        if self.redis_client:
            asyncio.create_task(self.redis_client.close())
        
        if self.db_connection:
            self.db_connection.close()
        
        logger.info("Model Performance Monitor shutdown complete")

# Alert handlers
def email_alert_handler(alert: Alert):
    """Example email alert handler"""
    logger.info(f"EMAIL ALERT: {alert.severity.value.upper()} - {alert.message}")

def slack_alert_handler(alert: Alert):
    """Example Slack alert handler"""
    logger.info(f"SLACK ALERT: {alert.severity.value.upper()} - {alert.message}")

def pagerduty_alert_handler(alert: Alert):
    """Example PagerDuty alert handler"""
    if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.HIGH]:
        logger.info(f"PAGERDUTY ALERT: {alert.severity.value.upper()} - {alert.message}")

# Usage example
async def demo_performance_monitoring():
    """Demonstrate performance monitoring system"""
    
    # Initialize monitor
    monitor = ModelPerformanceMonitor()
    await monitor.initialize()
    
    # Add alert handlers
    monitor.add_alert_handler(email_alert_handler)
    monitor.add_alert_handler(slack_alert_handler)
    monitor.add_alert_handler(pagerduty_alert_handler)
    
    # Simulate model predictions and metrics
    model_id = "sentiment_classifier_v1"
    
    for i in range(100):
        # Simulate metrics
        accuracy = 0.92 + np.random.normal(0, 0.05)
        latency = 150 + np.random.normal(0, 50)
        
        monitor.record_metric(model_id, "accuracy", accuracy)
        monitor.record_metric(model_id, "latency", latency)
        
        # Simulate medical metrics
        if i % 10 == 0:
            await monitor.record_medical_metrics(
                model_id,
                "Patient presents with acute chest pain and shortness of breath.",
                "Patient has acute chest pain with dyspnea."
            )
        
        await asyncio.sleep(0.1)
    
    # Get dashboard data
    dashboard = monitor.create_performance_dashboard(model_id)
    print(f"Dashboard created for {model_id}")
    print(f"Current metrics: {dashboard['current_metrics']}")
    print(f"Active alerts: {len(dashboard['active_alerts'])}")
    
    # Check alerts
    alerts = monitor.get_active_alerts()
    for alert in alerts:
        print(f"Alert: {alert.message}")
    
    monitor.shutdown()

if __name__ == "__main__":
    asyncio.run(demo_performance_monitoring())