#!/usr/bin/env python3
"""
AI Performance Monitoring System
Real-time performance metrics collection, analysis, and alerting for AI operations
"""

import time
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
import statistics
import json
import threading
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of performance metrics"""
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ACCURACY = "accuracy"
    ERROR_RATE = "error_rate"
    RESOURCE_USAGE = "resource_usage"
    COST = "cost"
    AVAILABILITY = "availability"

class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ResourceUsage:
    """Resource utilization metrics"""
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    gpu_percent: float = 0.0
    network_mbps: float = 0.0
    storage_mb: float = 0.0

@dataclass
class RequestMetrics:
    """Metrics for a single AI request"""
    request_id: str
    model_id: str
    provider: str
    start_time: datetime
    end_time: datetime
    latency_ms: float
    success: bool
    error_type: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    quality_score: float = 0.0
    resource_usage: ResourceUsage = field(default_factory=ResourceUsage)

@dataclass
class PerformanceMetrics:
    """Aggregated performance metrics"""
    model_id: str
    provider: str
    timeframe_start: datetime
    timeframe_end: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    throughput_rps: float
    error_rate: float
    avg_quality_score: float
    total_cost: float
    avg_cost_per_request: float
    resource_usage: ResourceUsage

@dataclass
class AlertThreshold:
    """Performance alert threshold configuration"""
    metric_type: MetricType
    threshold_value: float
    comparison: str  # "gt", "lt", "eq"
    severity: AlertSeverity
    enabled: bool = True

@dataclass
class PerformanceAlert:
    """Performance alert notification"""
    id: str
    timestamp: datetime
    model_id: str
    provider: str
    metric_type: MetricType
    current_value: float
    threshold_value: float
    severity: AlertSeverity
    message: str
    resolved: bool = False

@dataclass
class TrendAnalysis:
    """Performance trend analysis results"""
    model_id: str
    metric_type: MetricType
    trend_direction: str  # "improving", "degrading", "stable"
    trend_strength: float  # 0.0 to 1.0
    prediction: float
    confidence: float
    analysis_period: timedelta
    data_points: int

class PerformanceMonitor:
    """Real-time performance monitoring system for AI operations"""
    
    def __init__(self, max_history_size: int = 10000):
        self.max_history_size = max_history_size
        self.request_history: deque = deque(maxlen=max_history_size)
        self.metrics_cache: Dict[str, PerformanceMetrics] = {}
        self.alert_thresholds: Dict[str, List[AlertThreshold]] = defaultdict(list)
        self.active_alerts: Dict[str, PerformanceAlert] = {}
        self.trend_data: Dict[str, List[float]] = defaultdict(list)
        
        # Thread-safe locks
        self._history_lock = threading.Lock()
        self._cache_lock = threading.Lock()
        self._alert_lock = threading.Lock()
        
        # Background monitoring
        self._monitoring_active = False
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        logger.info("Performance Monitor initialized")
    
    def start_monitoring(self):
        """Start background monitoring processes"""
        if not self._monitoring_active:
            self._monitoring_active = True
            self._executor.submit(self._background_analysis)
            self._executor.submit(self._alert_processor)
            logger.info("Background monitoring started")
    
    def stop_monitoring(self):
        """Stop background monitoring processes"""
        self._monitoring_active = False
        self._executor.shutdown(wait=True)
        logger.info("Background monitoring stopped")
    
    def track_request(self, request_metrics: RequestMetrics) -> None:
        """Track performance metrics for a single AI request"""
        try:
            with self._history_lock:
                self.request_history.append(request_metrics)
            
            # Update real-time metrics
            self._update_realtime_metrics(request_metrics)
            
            # Check for alerts
            self._check_alert_conditions(request_metrics)
            
            logger.debug(f"Tracked request {request_metrics.request_id} for model {request_metrics.model_id}")
            
        except Exception as e:
            logger.error(f"Error tracking request metrics: {e}")
    
    def get_performance_metrics(self, model_id: str, provider: str = None, 
                               timeframe: timedelta = None) -> Optional[PerformanceMetrics]:
        """Get aggregated performance metrics for a model"""
        try:
            if timeframe is None:
                timeframe = timedelta(hours=1)
            
            end_time = datetime.now()
            start_time = end_time - timeframe
            
            # Filter relevant requests
            relevant_requests = []
            with self._history_lock:
                for req in self.request_history:
                    if (req.model_id == model_id and 
                        (provider is None or req.provider == provider) and
                        start_time <= req.start_time <= end_time):
                        relevant_requests.append(req)
            
            if not relevant_requests:
                return None
            
            # Calculate aggregated metrics
            return self._calculate_aggregated_metrics(
                relevant_requests, model_id, provider or "all", start_time, end_time
            )
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return None
    
    def get_realtime_metrics(self, model_id: str) -> Dict[str, Any]:
        """Get real-time performance metrics for a model"""
        try:
            cache_key = f"{model_id}_realtime"
            with self._cache_lock:
                if cache_key in self.metrics_cache:
                    metrics = self.metrics_cache[cache_key]
                    return {
                        "model_id": metrics.model_id,
                        "current_throughput": metrics.throughput_rps,
                        "avg_latency": metrics.avg_latency_ms,
                        "error_rate": metrics.error_rate,
                        "total_requests": metrics.total_requests,
                        "last_updated": metrics.timeframe_end.isoformat()
                    }
            return {}
            
        except Exception as e:
            logger.error(f"Error getting real-time metrics: {e}")
            return {}
    
    def analyze_trends(self, model_id: str, metric_type: MetricType, 
                      period: timedelta = None) -> Optional[TrendAnalysis]:
        """Analyze performance trends for a model and metric"""
        try:
            if period is None:
                period = timedelta(days=7)
            
            trend_key = f"{model_id}_{metric_type.value}"
            
            # Get historical data points
            data_points = self._get_trend_data(model_id, metric_type, period)
            
            if len(data_points) < 3:
                return None
            
            # Calculate trend
            trend_direction, trend_strength = self._calculate_trend(data_points)
            
            # Make prediction
            prediction = self._predict_next_value(data_points)
            confidence = min(len(data_points) / 100.0, 1.0)  # More data = higher confidence
            
            return TrendAnalysis(
                model_id=model_id,
                metric_type=metric_type,
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                prediction=prediction,
                confidence=confidence,
                analysis_period=period,
                data_points=len(data_points)
            )
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return None
    
    def set_alert_threshold(self, model_id: str, threshold: AlertThreshold) -> None:
        """Set performance alert threshold for a model"""
        try:
            with self._alert_lock:
                self.alert_thresholds[model_id].append(threshold)
            
            logger.info(f"Set alert threshold for {model_id}: {threshold.metric_type.value} {threshold.comparison} {threshold.threshold_value}")
            
        except Exception as e:
            logger.error(f"Error setting alert threshold: {e}")
    
    def get_active_alerts(self, model_id: str = None) -> List[PerformanceAlert]:
        """Get active performance alerts"""
        try:
            with self._alert_lock:
                alerts = list(self.active_alerts.values())
            
            if model_id:
                alerts = [alert for alert in alerts if alert.model_id == model_id]
            
            return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return []
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve a performance alert"""
        try:
            with self._alert_lock:
                if alert_id in self.active_alerts:
                    self.active_alerts[alert_id].resolved = True
                    logger.info(f"Resolved alert {alert_id}")
                    return True
            return False
            
        except Exception as e:
            logger.error(f"Error resolving alert: {e}")
            return False
    
    def get_model_comparison(self, model_ids: List[str], 
                           metric_type: MetricType = MetricType.LATENCY,
                           timeframe: timedelta = None) -> Dict[str, Any]:
        """Compare performance metrics across multiple models"""
        try:
            if timeframe is None:
                timeframe = timedelta(hours=1)
            
            comparison_data = {}
            
            for model_id in model_ids:
                metrics = self.get_performance_metrics(model_id, timeframe=timeframe)
                if metrics:
                    if metric_type == MetricType.LATENCY:
                        value = metrics.avg_latency_ms
                    elif metric_type == MetricType.THROUGHPUT:
                        value = metrics.throughput_rps
                    elif metric_type == MetricType.ERROR_RATE:
                        value = metrics.error_rate
                    elif metric_type == MetricType.COST:
                        value = metrics.avg_cost_per_request
                    else:
                        value = 0.0
                    
                    comparison_data[model_id] = {
                        "value": value,
                        "total_requests": metrics.total_requests,
                        "success_rate": (metrics.successful_requests / metrics.total_requests) * 100
                    }
            
            # Rank models
            if comparison_data:
                reverse_sort = metric_type in [MetricType.THROUGHPUT]  # Higher is better
                sorted_models = sorted(
                    comparison_data.items(), 
                    key=lambda x: x[1]["value"], 
                    reverse=reverse_sort
                )
                
                return {
                    "metric_type": metric_type.value,
                    "timeframe_hours": timeframe.total_seconds() / 3600,
                    "rankings": sorted_models,
                    "best_model": sorted_models[0][0] if sorted_models else None
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error comparing models: {e}")
            return {}
    
    def export_metrics(self, format_type: str = "json") -> str:
        """Export performance metrics in specified format"""
        try:
            export_data = {
                "timestamp": datetime.now().isoformat(),
                "total_requests": len(self.request_history),
                "active_alerts": len([a for a in self.active_alerts.values() if not a.resolved]),
                "models": {}
            }
            
            # Get unique models
            models = set()
            with self._history_lock:
                for req in self.request_history:
                    models.add(req.model_id)
            
            # Export metrics for each model
            for model_id in models:
                metrics = self.get_performance_metrics(model_id)
                if metrics:
                    export_data["models"][model_id] = asdict(metrics)
            
            if format_type.lower() == "json":
                return json.dumps(export_data, indent=2, default=str)
            else:
                raise ValueError(f"Unsupported export format: {format_type}")
                
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            return "{}"
    
    def _update_realtime_metrics(self, request_metrics: RequestMetrics) -> None:
        """Update real-time metrics cache"""
        try:
            cache_key = f"{request_metrics.model_id}_realtime"
            
            # Get recent requests for this model (last 5 minutes)
            recent_cutoff = datetime.now() - timedelta(minutes=5)
            recent_requests = []
            
            with self._history_lock:
                for req in reversed(self.request_history):
                    if req.model_id == request_metrics.model_id and req.start_time >= recent_cutoff:
                        recent_requests.append(req)
                    elif req.start_time < recent_cutoff:
                        break
            
            if recent_requests:
                metrics = self._calculate_aggregated_metrics(
                    recent_requests, 
                    request_metrics.model_id, 
                    request_metrics.provider,
                    recent_cutoff,
                    datetime.now()
                )
                
                with self._cache_lock:
                    self.metrics_cache[cache_key] = metrics
                    
        except Exception as e:
            logger.error(f"Error updating real-time metrics: {e}")
    
    def _calculate_aggregated_metrics(self, requests: List[RequestMetrics], 
                                    model_id: str, provider: str,
                                    start_time: datetime, end_time: datetime) -> PerformanceMetrics:
        """Calculate aggregated performance metrics from request list"""
        total_requests = len(requests)
        successful_requests = sum(1 for req in requests if req.success)
        failed_requests = total_requests - successful_requests
        
        latencies = [req.latency_ms for req in requests]
        costs = [req.cost for req in requests]
        quality_scores = [req.quality_score for req in requests if req.quality_score > 0]
        
        # Calculate percentiles
        latencies_sorted = sorted(latencies)
        p95_latency = latencies_sorted[int(0.95 * len(latencies_sorted))] if latencies_sorted else 0
        p99_latency = latencies_sorted[int(0.99 * len(latencies_sorted))] if latencies_sorted else 0
        
        # Calculate throughput (requests per second)
        duration_seconds = (end_time - start_time).total_seconds()
        throughput_rps = total_requests / duration_seconds if duration_seconds > 0 else 0
        
        # Aggregate resource usage
        cpu_usage = statistics.mean([req.resource_usage.cpu_percent for req in requests]) if requests else 0
        memory_usage = statistics.mean([req.resource_usage.memory_mb for req in requests]) if requests else 0
        gpu_usage = statistics.mean([req.resource_usage.gpu_percent for req in requests]) if requests else 0
        
        return PerformanceMetrics(
            model_id=model_id,
            provider=provider,
            timeframe_start=start_time,
            timeframe_end=end_time,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_latency_ms=statistics.mean(latencies) if latencies else 0,
            p95_latency_ms=p95_latency,
            p99_latency_ms=p99_latency,
            throughput_rps=throughput_rps,
            error_rate=(failed_requests / total_requests) * 100 if total_requests > 0 else 0,
            avg_quality_score=statistics.mean(quality_scores) if quality_scores else 0,
            total_cost=sum(costs),
            avg_cost_per_request=statistics.mean(costs) if costs else 0,
            resource_usage=ResourceUsage(
                cpu_percent=cpu_usage,
                memory_mb=memory_usage,
                gpu_percent=gpu_usage
            )
        )
    
    def _check_alert_conditions(self, request_metrics: RequestMetrics) -> None:
        """Check if request metrics trigger any alert conditions"""
        try:
            model_thresholds = self.alert_thresholds.get(request_metrics.model_id, [])
            
            for threshold in model_thresholds:
                if not threshold.enabled:
                    continue
                
                # Get current metric value
                current_value = self._get_metric_value(request_metrics, threshold.metric_type)
                
                # Check threshold condition
                triggered = False
                if threshold.comparison == "gt" and current_value > threshold.threshold_value:
                    triggered = True
                elif threshold.comparison == "lt" and current_value < threshold.threshold_value:
                    triggered = True
                elif threshold.comparison == "eq" and abs(current_value - threshold.threshold_value) < 0.001:
                    triggered = True
                
                if triggered:
                    self._create_alert(request_metrics, threshold, current_value)
                    
        except Exception as e:
            logger.error(f"Error checking alert conditions: {e}")
    
    def _get_metric_value(self, request_metrics: RequestMetrics, metric_type: MetricType) -> float:
        """Extract metric value from request metrics"""
        if metric_type == MetricType.LATENCY:
            return request_metrics.latency_ms
        elif metric_type == MetricType.COST:
            return request_metrics.cost
        elif metric_type == MetricType.ERROR_RATE:
            return 100.0 if not request_metrics.success else 0.0
        elif metric_type == MetricType.RESOURCE_USAGE:
            return request_metrics.resource_usage.cpu_percent
        else:
            return 0.0
    
    def _create_alert(self, request_metrics: RequestMetrics, 
                     threshold: AlertThreshold, current_value: float) -> None:
        """Create a new performance alert"""
        try:
            alert_id = f"{request_metrics.model_id}_{threshold.metric_type.value}_{int(time.time())}"
            
            alert = PerformanceAlert(
                id=alert_id,
                timestamp=datetime.now(),
                model_id=request_metrics.model_id,
                provider=request_metrics.provider,
                metric_type=threshold.metric_type,
                current_value=current_value,
                threshold_value=threshold.threshold_value,
                severity=threshold.severity,
                message=f"{threshold.metric_type.value} {threshold.comparison} {threshold.threshold_value} (current: {current_value})"
            )
            
            with self._alert_lock:
                self.active_alerts[alert_id] = alert
            
            logger.warning(f"Performance alert created: {alert.message}")
            
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
    
    def _get_trend_data(self, model_id: str, metric_type: MetricType, 
                       period: timedelta) -> List[float]:
        """Get historical data points for trend analysis"""
        try:
            end_time = datetime.now()
            start_time = end_time - period
            
            # Use smaller buckets for better trend detection (10 minutes for short periods, 1 hour for long)
            bucket_minutes = 10 if period.total_seconds() < 3600 * 6 else 60
            bucket_size = timedelta(minutes=bucket_minutes)
            buckets = {}
            
            with self._history_lock:
                for req in self.request_history:
                    if (req.model_id == model_id and 
                        start_time <= req.start_time <= end_time):
                        
                        # Determine bucket - round down to bucket boundary
                        minutes_since_start = int((req.start_time - start_time).total_seconds() / 60)
                        bucket_index = (minutes_since_start // bucket_minutes) * bucket_minutes
                        bucket_time = start_time + timedelta(minutes=bucket_index)
                        
                        if bucket_time not in buckets:
                            buckets[bucket_time] = []
                        
                        value = self._get_metric_value(req, metric_type)
                        buckets[bucket_time].append(value)
            
            # Calculate average for each bucket and ensure chronological order
            data_points = []
            for bucket_time in sorted(buckets.keys()):
                if buckets[bucket_time]:  # Only include buckets with data
                    avg_value = statistics.mean(buckets[bucket_time])
                    data_points.append(avg_value)
            
            return data_points
            
        except Exception as e:
            logger.error(f"Error getting trend data: {e}")
            return []
    
    def _calculate_trend(self, data_points: List[float]) -> tuple[str, float]:
        """Calculate trend direction and strength"""
        try:
            if len(data_points) < 2:
                return "stable", 0.0
            
            # Simple linear regression
            n = len(data_points)
            x_values = list(range(n))
            
            # Calculate slope
            x_mean = statistics.mean(x_values)
            y_mean = statistics.mean(data_points)
            
            numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, data_points))
            denominator = sum((x - x_mean) ** 2 for x in x_values)
            
            if denominator == 0:
                return "stable", 0.0
            
            slope = numerator / denominator
            
            # Calculate relative slope based on data range
            data_range = max(data_points) - min(data_points)
            if data_range > 0:
                relative_slope = abs(slope) / data_range
            else:
                relative_slope = 0.0
            
            # Determine trend direction and strength
            # For latency and error_rate: increasing = degrading, decreasing = improving
            # For throughput: increasing = improving, decreasing = degrading
            stability_threshold = 0.1  # 10% change relative to range
            
            if relative_slope < stability_threshold:
                return "stable", relative_slope
            elif slope > 0:
                # Increasing trend - check if this is good or bad based on metric
                return "degrading", min(relative_slope, 1.0)  # For latency, increasing is bad
            else:
                # Decreasing trend
                return "improving", min(relative_slope, 1.0)  # For latency, decreasing is good
                
        except Exception as e:
            logger.error(f"Error calculating trend: {e}")
            return "stable", 0.0
    
    def _predict_next_value(self, data_points: List[float]) -> float:
        """Predict next value based on trend"""
        try:
            if len(data_points) < 2:
                return data_points[0] if data_points else 0.0
            
            # Simple linear extrapolation
            recent_points = data_points[-3:]  # Use last 3 points
            if len(recent_points) >= 2:
                slope = (recent_points[-1] - recent_points[0]) / (len(recent_points) - 1)
                return recent_points[-1] + slope
            
            return data_points[-1]
            
        except Exception as e:
            logger.error(f"Error predicting next value: {e}")
            return 0.0
    
    def _background_analysis(self):
        """Background thread for continuous analysis"""
        while self._monitoring_active:
            try:
                # Update trend data every 5 minutes
                time.sleep(300)
                
                if not self._monitoring_active:
                    break
                
                # Analyze trends for all models
                models = set()
                with self._history_lock:
                    for req in list(self.request_history)[-1000:]:  # Last 1000 requests
                        models.add(req.model_id)
                
                for model_id in models:
                    for metric_type in [MetricType.LATENCY, MetricType.ERROR_RATE, MetricType.COST]:
                        trend = self.analyze_trends(model_id, metric_type)
                        if trend and trend.trend_direction == "degrading" and trend.trend_strength > 0.5:
                            logger.warning(f"Performance degradation detected for {model_id}: {metric_type.value}")
                
            except Exception as e:
                logger.error(f"Error in background analysis: {e}")
    
    def _alert_processor(self):
        """Background thread for alert processing"""
        while self._monitoring_active:
            try:
                time.sleep(60)  # Check every minute
                
                if not self._monitoring_active:
                    break
                
                # Auto-resolve old alerts (older than 1 hour)
                cutoff_time = datetime.now() - timedelta(hours=1)
                
                with self._alert_lock:
                    alerts_to_remove = []
                    for alert_id, alert in self.active_alerts.items():
                        if alert.timestamp < cutoff_time and not alert.resolved:
                            alert.resolved = True
                            alerts_to_remove.append(alert_id)
                    
                    for alert_id in alerts_to_remove:
                        logger.info(f"Auto-resolved old alert: {alert_id}")
                
            except Exception as e:
                logger.error(f"Error in alert processor: {e}")

# Export main classes
__all__ = [
    'PerformanceMonitor',
    'RequestMetrics',
    'PerformanceMetrics',
    'AlertThreshold',
    'PerformanceAlert',
    'TrendAnalysis',
    'MetricType',
    'AlertSeverity',
    'ResourceUsage'
]