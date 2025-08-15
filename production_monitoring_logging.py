"""
Production Monitoring & Logging System

A comprehensive monitoring and logging infrastructure supporting:
- Structured logging with correlation IDs
- Metrics collection (Prometheus/Grafana compatible)
- Health check endpoints for all services
- Error tracking and alerting
- Performance monitoring and profiling
- Database query optimization and monitoring
- Real-time dashboards for operations
- Log aggregation and analysis

Author: Production Team
Date: 2025-08-15
Version: 1.0.0
"""

import os
import json
import time
import uuid
import asyncio
import logging
import threading
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import sqlite3
from contextlib import contextmanager
import functools
from collections import defaultdict, deque
import statistics

# Core monitoring dependencies
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("psutil not available - system monitoring limited")

try:
    import prometheus_client
    from prometheus_client import Counter, Histogram, Gauge, Summary
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    print("prometheus_client not available - using basic metrics")

try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False
    print("structlog not available - using standard logging")

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("Redis not available - using in-memory storage")

try:
    import aiohttp
    import asyncio
    HTTP_AVAILABLE = True
except ImportError:
    HTTP_AVAILABLE = False
    print("aiohttp not available - health checks limited")

try:
    import pandas as pd
    import numpy as np
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False
    print("Analytics libraries not available - basic reporting only")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Log levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """Metric types"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HealthStatus(Enum):
    """Health check status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: datetime
    level: LogLevel
    message: str
    correlation_id: str
    service: str
    module: str
    function: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    duration: Optional[float] = None
    status_code: Optional[int] = None
    error: Optional[str] = None
    stack_trace: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Metric:
    """System metric"""
    name: str
    metric_type: MetricType
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    help_text: Optional[str] = None


@dataclass
class Alert:
    """System alert"""
    alert_id: str
    name: str
    severity: AlertSeverity
    message: str
    service: str
    metric: str
    threshold: float
    current_value: float
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    status: str = "active"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthCheck:
    """Health check result"""
    service: str
    status: HealthStatus
    message: str
    response_time: float
    timestamp: datetime
    dependencies: Dict[str, HealthStatus] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """Performance metrics collection"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    request_rate: float
    error_rate: float
    response_time_p95: float
    active_connections: int
    timestamp: datetime


class CorrelationIdManager:
    """Manages correlation IDs for request tracing"""
    
    def __init__(self):
        self._local = threading.local()
    
    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for current thread"""
        self._local.correlation_id = correlation_id
    
    def get_correlation_id(self) -> str:
        """Get correlation ID for current thread"""
        if not hasattr(self._local, 'correlation_id'):
            self._local.correlation_id = str(uuid.uuid4())
        return self._local.correlation_id
    
    def generate_correlation_id(self) -> str:
        """Generate new correlation ID"""
        correlation_id = str(uuid.uuid4())
        self.set_correlation_id(correlation_id)
        return correlation_id


class StructuredLogger:
    """Enhanced structured logging with correlation IDs"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.correlation_manager = CorrelationIdManager()
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup structured logger"""
        if STRUCTLOG_AVAILABLE:
            structlog.configure(
                processors=[
                    structlog.stdlib.filter_by_level,
                    structlog.stdlib.add_logger_name,
                    structlog.stdlib.add_log_level,
                    structlog.stdlib.PositionalArgumentsFormatter(),
                    structlog.processors.TimeStamper(fmt="iso"),
                    structlog.processors.StackInfoRenderer(),
                    structlog.processors.format_exc_info,
                    structlog.processors.UnicodeDecoder(),
                    structlog.processors.JSONRenderer()
                ],
                context_class=dict,
                logger_factory=structlog.stdlib.LoggerFactory(),
                wrapper_class=structlog.stdlib.BoundLogger,
                cache_logger_on_first_use=True,
            )
            self.logger = structlog.get_logger(self.service_name)
        else:
            self.logger = logging.getLogger(self.service_name)
    
    def _get_context(self, **kwargs) -> Dict[str, Any]:
        """Get logging context with correlation ID"""
        context = {
            'correlation_id': self.correlation_manager.get_correlation_id(),
            'service': self.service_name,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }
        return context
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        context = self._get_context(**kwargs)
        if STRUCTLOG_AVAILABLE:
            self.logger.debug(message, **context)
        else:
            self.logger.debug(f"{message} | {json.dumps(context)}")
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        context = self._get_context(**kwargs)
        if STRUCTLOG_AVAILABLE:
            self.logger.info(message, **context)
        else:
            self.logger.info(f"{message} | {json.dumps(context)}")
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        context = self._get_context(**kwargs)
        if STRUCTLOG_AVAILABLE:
            self.logger.warning(message, **context)
        else:
            self.logger.warning(f"{message} | {json.dumps(context)}")
    
    def error(self, message: str, error: Exception = None, **kwargs):
        """Log error message"""
        context = self._get_context(**kwargs)
        if error:
            context['error'] = str(error)
            context['error_type'] = type(error).__name__
            context['stack_trace'] = traceback.format_exc()
        
        if STRUCTLOG_AVAILABLE:
            self.logger.error(message, **context)
        else:
            self.logger.error(f"{message} | {json.dumps(context)}")
    
    def critical(self, message: str, error: Exception = None, **kwargs):
        """Log critical message"""
        context = self._get_context(**kwargs)
        if error:
            context['error'] = str(error)
            context['error_type'] = type(error).__name__
            context['stack_trace'] = traceback.format_exc()
        
        if STRUCTLOG_AVAILABLE:
            self.logger.critical(message, **context)
        else:
            self.logger.critical(f"{message} | {json.dumps(context)}")


class MetricsCollector:
    """Collects and manages application metrics"""
    
    def __init__(self):
        self.metrics = {}
        self.metrics_history = defaultdict(lambda: deque(maxlen=1000))
        self._setup_prometheus_metrics()
    
    def _setup_prometheus_metrics(self):
        """Setup Prometheus metrics if available"""
        if PROMETHEUS_AVAILABLE:
            self.prom_metrics = {
                'requests_total': Counter('requests_total', 'Total requests', ['method', 'endpoint', 'status']),
                'request_duration': Histogram('request_duration_seconds', 'Request duration', ['method', 'endpoint']),
                'active_connections': Gauge('active_connections', 'Active connections'),
                'cpu_usage': Gauge('cpu_usage_percent', 'CPU usage percentage'),
                'memory_usage': Gauge('memory_usage_bytes', 'Memory usage in bytes'),
                'error_rate': Gauge('error_rate', 'Error rate percentage'),
            }
        else:
            self.prom_metrics = {}
    
    def increment_counter(self, name: str, labels: Dict[str, str] = None, value: float = 1):
        """Increment a counter metric"""
        labels = labels or {}
        key = f"{name}_{hash(frozenset(labels.items()))}"
        
        if key not in self.metrics:
            self.metrics[key] = 0
        self.metrics[key] += value
        
        # Update Prometheus metric
        if PROMETHEUS_AVAILABLE and name in self.prom_metrics:
            self.prom_metrics[name].labels(**labels).inc(value)
        
        # Store in history
        self.metrics_history[name].append({
            'timestamp': datetime.now(),
            'value': self.metrics[key],
            'labels': labels
        })
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge metric"""
        labels = labels or {}
        key = f"{name}_{hash(frozenset(labels.items()))}"
        
        self.metrics[key] = value
        
        # Update Prometheus metric
        if PROMETHEUS_AVAILABLE and name in self.prom_metrics:
            self.prom_metrics[name].labels(**labels).set(value)
        
        # Store in history
        self.metrics_history[name].append({
            'timestamp': datetime.now(),
            'value': value,
            'labels': labels
        })
    
    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Observe a histogram metric"""
        labels = labels or {}
        
        # Update Prometheus metric
        if PROMETHEUS_AVAILABLE and name in self.prom_metrics:
            self.prom_metrics[name].labels(**labels).observe(value)
        
        # Store in history
        self.metrics_history[name].append({
            'timestamp': datetime.now(),
            'value': value,
            'labels': labels
        })
    
    def get_metric(self, name: str) -> Optional[float]:
        """Get current metric value"""
        return self.metrics.get(name)
    
    def get_metric_history(self, name: str, minutes: int = 60) -> List[Dict]:
        """Get metric history for specified time window"""
        if name not in self.metrics_history:
            return []
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        history = list(self.metrics_history[name])
        
        return [
            entry for entry in history 
            if entry['timestamp'] > cutoff_time
        ]
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        summary = {}
        
        for name, history in self.metrics_history.items():
            if not history:
                continue
            
            recent_values = [entry['value'] for entry in list(history)[-10:]]
            
            summary[name] = {
                'current': recent_values[-1] if recent_values else 0,
                'average': statistics.mean(recent_values) if recent_values else 0,
                'min': min(recent_values) if recent_values else 0,
                'max': max(recent_values) if recent_values else 0,
                'count': len(history)
            }
        
        return summary


class SystemMonitor:
    """Monitors system resources and performance"""
    
    def __init__(self):
        self.monitoring = True
        self.metrics_collector = MetricsCollector()
        self.logger = StructuredLogger("system_monitor")
    
    def get_system_metrics(self) -> PerformanceMetrics:
        """Get current system performance metrics"""
        try:
            if PSUTIL_AVAILABLE:
                cpu_usage = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                network = psutil.net_io_counters()
                
                network_io = {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                }
            else:
                # Fallback values when psutil not available
                cpu_usage = 0.0
                memory_usage = 0.0
                disk_usage = 0.0
                network_io = {'bytes_sent': 0, 'bytes_recv': 0, 'packets_sent': 0, 'packets_recv': 0}
                
                return PerformanceMetrics(
                    cpu_usage=cpu_usage,
                    memory_usage=memory_usage,
                    disk_usage=disk_usage,
                    network_io=network_io,
                    request_rate=0.0,
                    error_rate=0.0,
                    response_time_p95=0.0,
                    active_connections=0,
                    timestamp=datetime.now()
                )
            
            # Calculate application metrics
            request_rate = self._calculate_request_rate()
            error_rate = self._calculate_error_rate()
            response_time_p95 = self._calculate_response_time_p95()
            active_connections = self._get_active_connections()
            
            metrics = PerformanceMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                network_io=network_io,
                request_rate=request_rate,
                error_rate=error_rate,
                response_time_p95=response_time_p95,
                active_connections=active_connections,
                timestamp=datetime.now()
            )
            
            # Update metrics collector
            self.metrics_collector.set_gauge('cpu_usage', cpu_usage)
            self.metrics_collector.set_gauge('memory_usage', memory.used)
            self.metrics_collector.set_gauge('active_connections', active_connections)
            self.metrics_collector.set_gauge('error_rate', error_rate)
            
            return metrics
            
        except Exception as e:
            self.logger.error("Failed to collect system metrics", error=e)
            return PerformanceMetrics(
                cpu_usage=0.0, memory_usage=0.0, disk_usage=0.0,
                network_io={}, request_rate=0.0, error_rate=0.0,
                response_time_p95=0.0, active_connections=0,
                timestamp=datetime.now()
            )
    
    def _calculate_request_rate(self) -> float:
        """Calculate requests per second"""
        history = self.metrics_collector.get_metric_history('requests_total', minutes=1)
        if len(history) < 2:
            return 0.0
        
        return len(history) / 60.0  # requests per second
    
    def _calculate_error_rate(self) -> float:
        """Calculate error rate percentage"""
        total_history = self.metrics_collector.get_metric_history('requests_total', minutes=5)
        error_history = [entry for entry in total_history if entry.get('labels', {}).get('status', '').startswith('5')]
        
        if not total_history:
            return 0.0
        
        return (len(error_history) / len(total_history)) * 100
    
    def _calculate_response_time_p95(self) -> float:
        """Calculate 95th percentile response time"""
        history = self.metrics_collector.get_metric_history('request_duration', minutes=5)
        if not history:
            return 0.0
        
        values = [entry['value'] for entry in history]
        if len(values) == 0:
            return 0.0
        
        values.sort()
        index = int(0.95 * len(values))
        return values[min(index, len(values) - 1)]
    
    def _get_active_connections(self) -> int:
        """Get number of active connections"""
        if PSUTIL_AVAILABLE:
            try:
                connections = psutil.net_connections()
                return len([c for c in connections if c.status == 'ESTABLISHED'])
            except:
                return 0
        return 0
    
    async def start_monitoring(self, interval: int = 60):
        """Start continuous system monitoring"""
        self.logger.info("Starting system monitoring", interval=interval)
        
        while self.monitoring:
            try:
                metrics = self.get_system_metrics()
                self.logger.debug("System metrics collected", 
                                cpu=metrics.cpu_usage,
                                memory=metrics.memory_usage,
                                error_rate=metrics.error_rate)
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                self.logger.error("Error in monitoring loop", error=e)
                await asyncio.sleep(interval)
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        self.monitoring = False
        self.logger.info("System monitoring stopped")


class AlertManager:
    """Manages alerts and notifications"""
    
    def __init__(self):
        self.alerts = {}
        self.alert_rules = []
        self.logger = StructuredLogger("alert_manager")
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Setup default alerting rules"""
        self.alert_rules = [
            {
                'name': 'High CPU Usage',
                'metric': 'cpu_usage',
                'condition': 'greater_than',
                'threshold': 80.0,
                'severity': AlertSeverity.HIGH,
                'duration': 300  # 5 minutes
            },
            {
                'name': 'High Memory Usage',
                'metric': 'memory_usage',
                'condition': 'greater_than',
                'threshold': 85.0,
                'severity': AlertSeverity.HIGH,
                'duration': 300
            },
            {
                'name': 'High Error Rate',
                'metric': 'error_rate',
                'condition': 'greater_than',
                'threshold': 5.0,
                'severity': AlertSeverity.CRITICAL,
                'duration': 60
            },
            {
                'name': 'Low Disk Space',
                'metric': 'disk_usage',
                'condition': 'greater_than',
                'threshold': 90.0,
                'severity': AlertSeverity.CRITICAL,
                'duration': 0
            }
        ]
    
    def check_alerts(self, metrics: PerformanceMetrics):
        """Check metrics against alert rules"""
        for rule in self.alert_rules:
            metric_name = rule['metric']
            threshold = rule['threshold']
            condition = rule['condition']
            
            # Get metric value
            if hasattr(metrics, metric_name):
                current_value = getattr(metrics, metric_name)
            else:
                continue
            
            # Check condition
            alert_triggered = False
            if condition == 'greater_than' and current_value > threshold:
                alert_triggered = True
            elif condition == 'less_than' and current_value < threshold:
                alert_triggered = True
            
            alert_key = f"{rule['name']}_{metric_name}"
            
            if alert_triggered:
                if alert_key not in self.alerts:
                    # Create new alert
                    alert = Alert(
                        alert_id=str(uuid.uuid4()),
                        name=rule['name'],
                        severity=rule['severity'],
                        message=f"{rule['name']}: {metric_name} is {current_value:.2f}, threshold is {threshold}",
                        service="system",
                        metric=metric_name,
                        threshold=threshold,
                        current_value=current_value,
                        triggered_at=datetime.now()
                    )
                    
                    self.alerts[alert_key] = alert
                    self.logger.warning("Alert triggered", 
                                      alert_name=rule['name'],
                                      metric=metric_name,
                                      value=current_value,
                                      threshold=threshold)
            else:
                # Resolve alert if it exists
                if alert_key in self.alerts:
                    self.alerts[alert_key].resolved_at = datetime.now()
                    self.alerts[alert_key].status = "resolved"
                    self.logger.info("Alert resolved",
                                   alert_name=rule['name'],
                                   metric=metric_name,
                                   value=current_value)
    
    def get_active_alerts(self) -> List[Alert]:
        """Get list of active alerts"""
        return [alert for alert in self.alerts.values() if alert.status == "active"]
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary statistics"""
        active_alerts = self.get_active_alerts()
        
        severity_counts = defaultdict(int)
        for alert in active_alerts:
            severity_counts[alert.severity.value] += 1
        
        return {
            'total_active': len(active_alerts),
            'by_severity': dict(severity_counts),
            'last_updated': datetime.now().isoformat()
        }


class HealthChecker:
    """Performs health checks on system components"""
    
    def __init__(self):
        self.logger = StructuredLogger("health_checker")
        self.health_checks = {}
    
    async def check_database_health(self, db_path: str) -> HealthCheck:
        """Check database connectivity and performance"""
        start_time = time.time()
        
        try:
            with sqlite3.connect(db_path, timeout=5) as conn:
                cursor = conn.execute("SELECT 1")
                cursor.fetchone()
            
            response_time = time.time() - start_time
            
            return HealthCheck(
                service="database",
                status=HealthStatus.HEALTHY,
                message="Database connection successful",
                response_time=response_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheck(
                service="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}",
                response_time=response_time,
                timestamp=datetime.now()
            )
    
    async def check_external_service_health(self, service_name: str, url: str) -> HealthCheck:
        """Check external service health"""
        start_time = time.time()
        
        try:
            if HTTP_AVAILABLE:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                    async with session.get(url) as response:
                        response_time = time.time() - start_time
                        
                        if response.status == 200:
                            status = HealthStatus.HEALTHY
                            message = "Service responding normally"
                        elif response.status < 500:
                            status = HealthStatus.DEGRADED
                            message = f"Service returned status {response.status}"
                        else:
                            status = HealthStatus.UNHEALTHY
                            message = f"Service error: status {response.status}"
            else:
                # Fallback when aiohttp not available
                response_time = 0.1
                status = HealthStatus.UNKNOWN
                message = "HTTP client not available for health check"
            
            return HealthCheck(
                service=service_name,
                status=status,
                message=message,
                response_time=response_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheck(
                service=service_name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
                response_time=response_time,
                timestamp=datetime.now()
            )
    
    async def check_system_resources(self) -> HealthCheck:
        """Check system resource health"""
        start_time = time.time()
        
        try:
            if PSUTIL_AVAILABLE:
                cpu = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # Determine health status based on resource usage
                if cpu > 90 or memory.percent > 95 or disk.percent > 95:
                    status = HealthStatus.UNHEALTHY
                    message = "Critical resource usage"
                elif cpu > 80 or memory.percent > 85 or disk.percent > 90:
                    status = HealthStatus.DEGRADED
                    message = "High resource usage"
                else:
                    status = HealthStatus.HEALTHY
                    message = "Resource usage normal"
                
                dependencies = {
                    'cpu': HealthStatus.HEALTHY if cpu < 80 else HealthStatus.DEGRADED,
                    'memory': HealthStatus.HEALTHY if memory.percent < 85 else HealthStatus.DEGRADED,
                    'disk': HealthStatus.HEALTHY if disk.percent < 90 else HealthStatus.DEGRADED
                }
            else:
                status = HealthStatus.UNKNOWN
                message = "System monitoring not available"
                dependencies = {}
            
            response_time = time.time() - start_time
            
            return HealthCheck(
                service="system_resources",
                status=status,
                message=message,
                response_time=response_time,
                timestamp=datetime.now(),
                dependencies=dependencies
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheck(
                service="system_resources",
                status=HealthStatus.UNHEALTHY,
                message=f"Resource check failed: {str(e)}",
                response_time=response_time,
                timestamp=datetime.now()
            )
    
    async def perform_comprehensive_health_check(self) -> Dict[str, HealthCheck]:
        """Perform comprehensive health check of all services"""
        self.logger.info("Starting comprehensive health check")
        
        health_checks = {}
        
        # Check system resources
        health_checks['system'] = await self.check_system_resources()
        
        # Check database (if path provided)
        db_path = os.getenv('DATABASE_PATH', 'production.db')
        if os.path.exists(db_path):
            health_checks['database'] = await self.check_database_health(db_path)
        
        # Check external services (example URLs)
        external_services = {
            'openai': 'https://api.openai.com/v1/models',
            'google_translate': 'https://translate.googleapis.com/',
        }
        
        for service_name, url in external_services.items():
            try:
                health_checks[service_name] = await self.check_external_service_health(service_name, url)
            except Exception as e:
                self.logger.error(f"Failed to check {service_name} health", error=e)
        
        # Overall health assessment
        overall_status = self._assess_overall_health(health_checks)
        
        self.logger.info("Health check completed", 
                        overall_status=overall_status.value,
                        services_checked=len(health_checks))
        
        return health_checks
    
    def _assess_overall_health(self, health_checks: Dict[str, HealthCheck]) -> HealthStatus:
        """Assess overall system health"""
        if not health_checks:
            return HealthStatus.UNKNOWN
        
        statuses = [check.status for check in health_checks.values()]
        
        if any(status == HealthStatus.UNHEALTHY for status in statuses):
            return HealthStatus.UNHEALTHY
        elif any(status == HealthStatus.DEGRADED for status in statuses):
            return HealthStatus.DEGRADED
        elif all(status == HealthStatus.HEALTHY for status in statuses):
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN


class MonitoringDatabase:
    """Database for storing monitoring data"""
    
    def __init__(self, db_path: str = "production_monitoring.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize monitoring database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                -- Log Entries
                CREATE TABLE IF NOT EXISTS log_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    correlation_id TEXT NOT NULL,
                    service TEXT NOT NULL,
                    module TEXT,
                    function TEXT,
                    user_id TEXT,
                    session_id TEXT,
                    request_id TEXT,
                    duration REAL,
                    status_code INTEGER,
                    error TEXT,
                    stack_trace TEXT,
                    metadata TEXT DEFAULT '{}'
                );
                
                -- Metrics
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    labels TEXT DEFAULT '{}',
                    help_text TEXT
                );
                
                -- Alerts
                CREATE TABLE IF NOT EXISTS alerts (
                    alert_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    service TEXT NOT NULL,
                    metric TEXT NOT NULL,
                    threshold REAL NOT NULL,
                    current_value REAL NOT NULL,
                    triggered_at TIMESTAMP NOT NULL,
                    resolved_at TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    metadata TEXT DEFAULT '{}'
                );
                
                -- Health Checks
                CREATE TABLE IF NOT EXISTS health_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT NOT NULL,
                    response_time REAL NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    dependencies TEXT DEFAULT '{}',
                    metadata TEXT DEFAULT '{}'
                );
                
                -- Performance Metrics
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cpu_usage REAL NOT NULL,
                    memory_usage REAL NOT NULL,
                    disk_usage REAL NOT NULL,
                    network_io TEXT NOT NULL,
                    request_rate REAL NOT NULL,
                    error_rate REAL NOT NULL,
                    response_time_p95 REAL NOT NULL,
                    active_connections INTEGER NOT NULL,
                    timestamp TIMESTAMP NOT NULL
                );
                
                -- Indexes for performance
                CREATE INDEX IF NOT EXISTS idx_log_entries_timestamp ON log_entries (timestamp);
                CREATE INDEX IF NOT EXISTS idx_log_entries_correlation ON log_entries (correlation_id);
                CREATE INDEX IF NOT EXISTS idx_log_entries_level ON log_entries (level);
                CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics (name);
                CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics (timestamp);
                CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts (status);
                CREATE INDEX IF NOT EXISTS idx_health_checks_service ON health_checks (service);
                CREATE INDEX IF NOT EXISTS idx_performance_timestamp ON performance_metrics (timestamp);
            """)
    
    def store_log_entry(self, log_entry: LogEntry):
        """Store log entry in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO log_entries (
                    timestamp, level, message, correlation_id, service,
                    module, function, user_id, session_id, request_id,
                    duration, status_code, error, stack_trace, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log_entry.timestamp.isoformat(), log_entry.level.value,
                log_entry.message, log_entry.correlation_id, log_entry.service,
                log_entry.module, log_entry.function, log_entry.user_id,
                log_entry.session_id, log_entry.request_id, log_entry.duration,
                log_entry.status_code, log_entry.error, log_entry.stack_trace,
                json.dumps(log_entry.metadata)
            ))
    
    def store_metric(self, metric: Metric):
        """Store metric in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO metrics (
                    name, metric_type, value, timestamp, labels, help_text
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                metric.name, metric.metric_type.value, metric.value,
                metric.timestamp.isoformat(), json.dumps(metric.labels),
                metric.help_text
            ))
    
    def store_alert(self, alert: Alert):
        """Store alert in database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO alerts (
                    alert_id, name, severity, message, service, metric,
                    threshold, current_value, triggered_at, resolved_at,
                    status, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.alert_id, alert.name, alert.severity.value,
                alert.message, alert.service, alert.metric,
                alert.threshold, alert.current_value,
                alert.triggered_at.isoformat(),
                alert.resolved_at.isoformat() if alert.resolved_at else None,
                alert.status, json.dumps(alert.metadata)
            ))
    
    def store_health_check(self, health_check: HealthCheck):
        """Store health check result"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO health_checks (
                    service, status, message, response_time, timestamp,
                    dependencies, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                health_check.service, health_check.status.value,
                health_check.message, health_check.response_time,
                health_check.timestamp.isoformat(),
                json.dumps({k: v.value for k, v in health_check.dependencies.items()}),
                json.dumps(health_check.metadata)
            ))
    
    def store_performance_metrics(self, metrics: PerformanceMetrics):
        """Store performance metrics"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO performance_metrics (
                    cpu_usage, memory_usage, disk_usage, network_io,
                    request_rate, error_rate, response_time_p95,
                    active_connections, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.cpu_usage, metrics.memory_usage, metrics.disk_usage,
                json.dumps(metrics.network_io), metrics.request_rate,
                metrics.error_rate, metrics.response_time_p95,
                metrics.active_connections, metrics.timestamp.isoformat()
            ))
    
    def get_monitoring_statistics(self) -> Dict[str, Any]:
        """Get comprehensive monitoring statistics"""
        with sqlite3.connect(self.db_path) as conn:
            # Log statistics
            cursor = conn.execute("""
                SELECT level, COUNT(*) 
                FROM log_entries 
                WHERE timestamp > datetime('now', '-24 hours')
                GROUP BY level
            """)
            log_stats = dict(cursor.fetchall())
            
            # Active alerts
            cursor = conn.execute("""
                SELECT severity, COUNT(*) 
                FROM alerts 
                WHERE status = 'active'
                GROUP BY severity
            """)
            alert_stats = dict(cursor.fetchall())
            
            # Health check summary
            cursor = conn.execute("""
                SELECT service, status, timestamp
                FROM health_checks 
                WHERE timestamp > datetime('now', '-1 hour')
                ORDER BY timestamp DESC
            """)
            health_data = cursor.fetchall()
            
            # Recent performance
            cursor = conn.execute("""
                SELECT AVG(cpu_usage), AVG(memory_usage), AVG(error_rate)
                FROM performance_metrics 
                WHERE timestamp > datetime('now', '-1 hour')
            """)
            perf_row = cursor.fetchone()
            
            performance_summary = {
                'avg_cpu': perf_row[0] if perf_row[0] else 0,
                'avg_memory': perf_row[1] if perf_row[1] else 0,
                'avg_error_rate': perf_row[2] if perf_row[2] else 0
            }
        
        return {
            'log_statistics': log_stats,
            'active_alerts': alert_stats,
            'health_status': len([h for h in health_data if h[1] == 'healthy']),
            'performance_summary': performance_summary,
            'last_updated': datetime.now().isoformat()
        }


class ProductionMonitoringLogging:
    """Main monitoring and logging system"""
    
    def __init__(self, service_name: str = "production_system", db_path: str = "production_monitoring.db"):
        self.service_name = service_name
        self.db = MonitoringDatabase(db_path)
        self.logger = StructuredLogger(service_name)
        self.metrics_collector = MetricsCollector()
        self.system_monitor = SystemMonitor()
        self.alert_manager = AlertManager()
        self.health_checker = HealthChecker()
        
        # Configuration
        self.config = {
            'monitoring_interval': 60,
            'health_check_interval': 300,
            'log_retention_days': 30,
            'metrics_retention_days': 7,
            'enable_alerts': True,
            'enable_health_checks': True,
            'log_level': LogLevel.INFO
        }
        
        self.monitoring_active = False
        
        logger.info("Production Monitoring & Logging System initialized")
    
    def monitoring_decorator(self, operation_name: str = None):
        """Decorator for monitoring function execution"""
        def decorator(func: Callable):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                op_name = operation_name or f"{func.__module__}.{func.__name__}"
                correlation_id = self.logger.correlation_manager.generate_correlation_id()
                
                start_time = time.time()
                self.logger.info(f"Starting {op_name}", 
                               operation=op_name,
                               correlation_id=correlation_id)
                
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    # Record metrics
                    self.metrics_collector.observe_histogram(
                        'request_duration',
                        duration,
                        {'operation': op_name, 'status': 'success'}
                    )
                    self.metrics_collector.increment_counter(
                        'requests_total',
                        {'operation': op_name, 'status': 'success'}
                    )
                    
                    self.logger.info(f"Completed {op_name}", 
                                   operation=op_name,
                                   duration=duration,
                                   status="success")
                    
                    return result
                    
                except Exception as e:
                    duration = time.time() - start_time
                    
                    # Record error metrics
                    self.metrics_collector.observe_histogram(
                        'request_duration',
                        duration,
                        {'operation': op_name, 'status': 'error'}
                    )
                    self.metrics_collector.increment_counter(
                        'requests_total',
                        {'operation': op_name, 'status': 'error'}
                    )
                    
                    self.logger.error(f"Failed {op_name}", 
                                    operation=op_name,
                                    duration=duration,
                                    error=e,
                                    status="error")
                    
                    raise
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                op_name = operation_name or f"{func.__module__}.{func.__name__}"
                correlation_id = self.logger.correlation_manager.generate_correlation_id()
                
                start_time = time.time()
                self.logger.info(f"Starting {op_name}", 
                               operation=op_name,
                               correlation_id=correlation_id)
                
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    # Record metrics
                    self.metrics_collector.observe_histogram(
                        'request_duration',
                        duration,
                        {'operation': op_name, 'status': 'success'}
                    )
                    self.metrics_collector.increment_counter(
                        'requests_total',
                        {'operation': op_name, 'status': 'success'}
                    )
                    
                    self.logger.info(f"Completed {op_name}", 
                                   operation=op_name,
                                   duration=duration,
                                   status="success")
                    
                    return result
                    
                except Exception as e:
                    duration = time.time() - start_time
                    
                    # Record error metrics
                    self.metrics_collector.observe_histogram(
                        'request_duration',
                        duration,
                        {'operation': op_name, 'status': 'error'}
                    )
                    self.metrics_collector.increment_counter(
                        'requests_total',
                        {'operation': op_name, 'status': 'error'}
                    )
                    
                    self.logger.error(f"Failed {op_name}", 
                                    operation=op_name,
                                    duration=duration,
                                    error=e,
                                    status="error")
                    
                    raise
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator
    
    async def start_monitoring(self):
        """Start comprehensive monitoring"""
        if self.monitoring_active:
            self.logger.warning("Monitoring already active")
            return
        
        self.monitoring_active = True
        self.logger.info("Starting comprehensive monitoring")
        
        # Start monitoring tasks
        tasks = []
        
        # System monitoring
        tasks.append(asyncio.create_task(
            self.system_monitor.start_monitoring(self.config['monitoring_interval'])
        ))
        
        # Health checks
        if self.config['enable_health_checks']:
            tasks.append(asyncio.create_task(
                self._health_check_loop()
            ))
        
        # Alert checking
        if self.config['enable_alerts']:
            tasks.append(asyncio.create_task(
                self._alert_check_loop()
            ))
        
        # Data persistence
        tasks.append(asyncio.create_task(
            self._data_persistence_loop()
        ))
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            self.logger.error("Monitoring task failed", error=e)
        finally:
            self.monitoring_active = False
    
    async def _health_check_loop(self):
        """Periodic health check loop"""
        while self.monitoring_active:
            try:
                health_checks = await self.health_checker.perform_comprehensive_health_check()
                
                for service, health_check in health_checks.items():
                    self.db.store_health_check(health_check)
                
                await asyncio.sleep(self.config['health_check_interval'])
                
            except Exception as e:
                self.logger.error("Health check loop failed", error=e)
                await asyncio.sleep(self.config['health_check_interval'])
    
    async def _alert_check_loop(self):
        """Periodic alert checking loop"""
        while self.monitoring_active:
            try:
                # Get current system metrics
                metrics = self.system_monitor.get_system_metrics()
                
                # Check for alerts
                self.alert_manager.check_alerts(metrics)
                
                # Store any new alerts
                for alert in self.alert_manager.alerts.values():
                    self.db.store_alert(alert)
                
                await asyncio.sleep(60)  # Check alerts every minute
                
            except Exception as e:
                self.logger.error("Alert check loop failed", error=e)
                await asyncio.sleep(60)
    
    async def _data_persistence_loop(self):
        """Periodic data persistence loop"""
        while self.monitoring_active:
            try:
                # Store current system metrics
                metrics = self.system_monitor.get_system_metrics()
                self.db.store_performance_metrics(metrics)
                
                await asyncio.sleep(300)  # Store metrics every 5 minutes
                
            except Exception as e:
                self.logger.error("Data persistence loop failed", error=e)
                await asyncio.sleep(300)
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring_active = False
        self.system_monitor.stop_monitoring()
        self.logger.info("Monitoring stopped")
    
    def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive monitoring dashboard data"""
        # Get system metrics
        system_metrics = self.system_monitor.get_system_metrics()
        
        # Get alert summary
        alert_summary = self.alert_manager.get_alert_summary()
        
        # Get metrics summary
        metrics_summary = self.metrics_collector.get_metrics_summary()
        
        # Get database statistics
        db_stats = self.db.get_monitoring_statistics()
        
        dashboard = {
            'system_status': {
                'cpu_usage': system_metrics.cpu_usage,
                'memory_usage': system_metrics.memory_usage,
                'disk_usage': system_metrics.disk_usage,
                'active_connections': system_metrics.active_connections,
                'request_rate': system_metrics.request_rate,
                'error_rate': system_metrics.error_rate,
                'response_time_p95': system_metrics.response_time_p95
            },
            'alerts': alert_summary,
            'metrics': metrics_summary,
            'database_stats': db_stats,
            'monitoring_config': self.config,
            'last_updated': datetime.now().isoformat()
        }
        
        return dashboard
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            'monitoring_active': self.monitoring_active,
            'service_name': self.service_name,
            'configuration': self.config,
            'features': {
                'structlog_available': STRUCTLOG_AVAILABLE,
                'prometheus_available': PROMETHEUS_AVAILABLE,
                'psutil_available': PSUTIL_AVAILABLE,
                'redis_available': REDIS_AVAILABLE,
                'http_available': HTTP_AVAILABLE,
                'analytics_available': ANALYTICS_AVAILABLE
            }
        }


# Demo and testing functions
async def demo_monitoring_logging():
    """Demonstrate the monitoring and logging system"""
    print("=== Production Monitoring & Logging System Demo ===\n")
    
    # Initialize system
    monitoring_system = ProductionMonitoringLogging("demo_service")
    
    # Get system status
    print("1. System Status:")
    status = monitoring_system.get_system_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    # Demo logging with correlation IDs
    print("\n2. Structured Logging Demo:")
    monitoring_system.logger.info("Demo started", user_id="demo_user", action="demo_start")
    monitoring_system.logger.warning("This is a warning", metric="demo_metric", value=42)
    monitoring_system.logger.error("This is an error demo", error=Exception("Demo error"))
    
    # Demo monitoring decorator
    print("\n3. Monitoring Decorator Demo:")
    
    @monitoring_system.monitoring_decorator("demo_operation")
    def demo_function(x, y):
        time.sleep(0.1)  # Simulate work
        return x + y
    
    result = demo_function(5, 3)
    print(f"   Function result: {result}")
    
    # Demo system metrics
    print("\n4. System Metrics:")
    metrics = monitoring_system.system_monitor.get_system_metrics()
    print(f"   CPU Usage: {metrics.cpu_usage:.1f}%")
    print(f"   Memory Usage: {metrics.memory_usage:.1f}%")
    print(f"   Error Rate: {metrics.error_rate:.2f}%")
    print(f"   Active Connections: {metrics.active_connections}")
    
    # Demo health checks
    print("\n5. Health Checks:")
    health_checks = await monitoring_system.health_checker.perform_comprehensive_health_check()
    for service, health in health_checks.items():
        print(f"   {service}: {health.status.value} ({health.response_time:.3f}s)")
    
    # Demo alerts
    print("\n6. Alert System:")
    # Simulate high CPU to trigger alert
    fake_metrics = PerformanceMetrics(
        cpu_usage=85.0,  # High CPU to trigger alert
        memory_usage=70.0,
        disk_usage=60.0,
        network_io={},
        request_rate=100.0,
        error_rate=2.0,
        response_time_p95=0.5,
        active_connections=50,
        timestamp=datetime.now()
    )
    monitoring_system.alert_manager.check_alerts(fake_metrics)
    active_alerts = monitoring_system.alert_manager.get_active_alerts()
    print(f"   Active alerts: {len(active_alerts)}")
    for alert in active_alerts:
        print(f"   - {alert.name}: {alert.message}")
    
    # Demo metrics collection
    print("\n7. Metrics Collection:")
    monitoring_system.metrics_collector.increment_counter('demo_requests', {'method': 'GET'})
    monitoring_system.metrics_collector.set_gauge('demo_connections', 25)
    monitoring_system.metrics_collector.observe_histogram('demo_duration', 0.15)
    
    metrics_summary = monitoring_system.metrics_collector.get_metrics_summary()
    print(f"   Metrics tracked: {len(metrics_summary)}")
    
    # Demo dashboard
    print("\n8. Monitoring Dashboard:")
    dashboard = monitoring_system.get_monitoring_dashboard()
    print(f"   System CPU: {dashboard['system_status']['cpu_usage']:.1f}%")
    print(f"   Active alerts: {dashboard['alerts']['total_active']}")
    print(f"   Metrics count: {len(dashboard['metrics'])}")
    
    print("\n✅ Monitoring & Logging demo completed successfully!")


if __name__ == "__main__":
    asyncio.run(demo_monitoring_logging())