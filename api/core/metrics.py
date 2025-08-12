"""
Metrics collection and monitoring
"""

import time
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta
import threading
import json

class MetricsCollector:
    """
    Comprehensive metrics collector for monitoring application performance
    """
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.counters = defaultdict(int)
        self.histograms = defaultdict(list)
        self.gauges = defaultdict(float)
        self.timers = {}
        self.start_time = time.time()
        self._lock = threading.Lock()
        
        # Keep metrics for the last hour by default
        self.retention_period = 3600  # 1 hour in seconds
        self.cleanup_interval = 300   # 5 minutes
        self.last_cleanup = time.time()
    
    def increment_counter(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        with self._lock:
            metric_key = self._build_metric_key(name, labels)
            self.counters[metric_key] += value
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set a gauge metric value"""
        with self._lock:
            metric_key = self._build_metric_key(name, labels)
            self.gauges[metric_key] = value
    
    def record_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a value in a histogram"""
        with self._lock:
            metric_key = self._build_metric_key(name, labels)
            timestamp = time.time()
            self.histograms[metric_key].append((timestamp, value))
            
            # Cleanup old values
            self._cleanup_histogram(metric_key)
    
    def start_timer(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """Start a timer and return timer ID"""
        timer_id = f"{name}_{int(time.time() * 1000000)}"
        metric_key = self._build_metric_key(name, labels)
        
        with self._lock:
            self.timers[timer_id] = {
                "metric_key": metric_key,
                "start_time": time.time()
            }
        
        return timer_id
    
    def stop_timer(self, timer_id: str) -> Optional[float]:
        """Stop a timer and record the duration"""
        with self._lock:
            if timer_id not in self.timers:
                return None
            
            timer_info = self.timers.pop(timer_id)
            duration = time.time() - timer_info["start_time"]
            
            # Record as histogram
            timestamp = time.time()
            self.histograms[timer_info["metric_key"]].append((timestamp, duration))
            self._cleanup_histogram(timer_info["metric_key"])
            
            return duration
    
    def record_timer(self, name: str, duration: float, labels: Optional[Dict[str, str]] = None):
        """Record a timer duration directly"""
        self.record_histogram(name, duration, labels)
    
    def get_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> int:
        """Get current counter value"""
        metric_key = self._build_metric_key(name, labels)
        return self.counters.get(metric_key, 0)
    
    def get_gauge(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Get current gauge value"""
        metric_key = self._build_metric_key(name, labels)
        return self.gauges.get(metric_key, 0.0)
    
    def get_histogram_stats(self, name: str, labels: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """Get histogram statistics"""
        metric_key = self._build_metric_key(name, labels)
        values = [v for _, v in self.histograms.get(metric_key, [])]
        
        if not values:
            return {
                "count": 0,
                "sum": 0.0,
                "min": 0.0,
                "max": 0.0,
                "avg": 0.0,
                "p50": 0.0,
                "p95": 0.0,
                "p99": 0.0
            }
        
        values.sort()
        count = len(values)
        
        return {
            "count": count,
            "sum": sum(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / count,
            "p50": self._percentile(values, 50),
            "p95": self._percentile(values, 95),
            "p99": self._percentile(values, 99)
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics in a structured format"""
        self._cleanup_old_metrics()
        
        with self._lock:
            metrics = {
                "service": self.service_name,
                "timestamp": datetime.utcnow().isoformat(),
                "uptime": time.time() - self.start_time,
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "histograms": {}
            }
            
            # Add histogram statistics
            for metric_key in self.histograms:
                name, labels = self._parse_metric_key(metric_key)
                stats = self.get_histogram_stats(name, labels)
                metrics["histograms"][metric_key] = stats
        
        return metrics
    
    def get_prometheus_format(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        
        # Add service info
        lines.append(f'# HELP service_info Service information')
        lines.append(f'# TYPE service_info gauge')
        lines.append(f'service_info{{service="{self.service_name}"}} 1')
        lines.append('')
        
        # Add uptime
        uptime = time.time() - self.start_time
        lines.append(f'# HELP service_uptime_seconds Service uptime in seconds')
        lines.append(f'# TYPE service_uptime_seconds gauge')
        lines.append(f'service_uptime_seconds{{service="{self.service_name}"}} {uptime}')
        lines.append('')
        
        with self._lock:
            # Export counters
            for metric_key, value in self.counters.items():
                name, labels = self._parse_metric_key(metric_key)
                labels_str = self._format_prometheus_labels(labels)
                lines.append(f'# TYPE {name} counter')
                lines.append(f'{name}{labels_str} {value}')
            
            # Export gauges
            for metric_key, value in self.gauges.items():
                name, labels = self._parse_metric_key(metric_key)
                labels_str = self._format_prometheus_labels(labels)
                lines.append(f'# TYPE {name} gauge')
                lines.append(f'{name}{labels_str} {value}')
            
            # Export histograms
            for metric_key in self.histograms:
                name, labels = self._parse_metric_key(metric_key)
                stats = self.get_histogram_stats(name, labels)
                labels_str = self._format_prometheus_labels(labels)
                
                lines.append(f'# TYPE {name} histogram')
                lines.append(f'{name}_count{labels_str} {stats["count"]}')
                lines.append(f'{name}_sum{labels_str} {stats["sum"]}')
                
                # Add percentile buckets
                for percentile in [50, 95, 99]:
                    bucket_labels = {**(labels or {}), "quantile": f"0.{percentile:02d}"}
                    bucket_labels_str = self._format_prometheus_labels(bucket_labels)
                    lines.append(f'{name}{bucket_labels_str} {stats[f"p{percentile}"]}')
        
        return '\n'.join(lines)
    
    def reset_metrics(self):
        """Reset all metrics"""
        with self._lock:
            self.counters.clear()
            self.histograms.clear()
            self.gauges.clear()
            self.timers.clear()
    
    def _build_metric_key(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """Build a unique key for a metric with labels"""
        if not labels:
            return name
        
        label_parts = [f"{k}={v}" for k, v in sorted(labels.items())]
        return f"{name}{{{','.join(label_parts)}}}"
    
    def _parse_metric_key(self, metric_key: str) -> tuple:
        """Parse a metric key back into name and labels"""
        if '{' not in metric_key:
            return metric_key, None
        
        name, labels_str = metric_key.split('{', 1)
        labels_str = labels_str.rstrip('}')
        
        labels = {}
        if labels_str:
            for label_pair in labels_str.split(','):
                key, value = label_pair.split('=', 1)
                labels[key] = value
        
        return name, labels if labels else None
    
    def _format_prometheus_labels(self, labels: Optional[Dict[str, str]]) -> str:
        """Format labels for Prometheus export"""
        if not labels:
            return ""
        
        label_parts = [f'{k}="{v}"' for k, v in sorted(labels.items())]
        return f'{{{",".join(label_parts)}}}'
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile from sorted values"""
        if not values:
            return 0.0
        
        index = (percentile / 100.0) * (len(values) - 1)
        lower_index = int(index)
        upper_index = min(lower_index + 1, len(values) - 1)
        
        if lower_index == upper_index:
            return values[lower_index]
        
        # Linear interpolation
        weight = index - lower_index
        return values[lower_index] * (1 - weight) + values[upper_index] * weight
    
    def _cleanup_histogram(self, metric_key: str):
        """Remove old values from histogram"""
        cutoff_time = time.time() - self.retention_period
        self.histograms[metric_key] = [
            (timestamp, value) for timestamp, value in self.histograms[metric_key]
            if timestamp > cutoff_time
        ]
    
    def _cleanup_old_metrics(self):
        """Periodic cleanup of old metrics"""
        current_time = time.time()
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        with self._lock:
            # Cleanup histograms
            for metric_key in list(self.histograms.keys()):
                self._cleanup_histogram(metric_key)
                
                # Remove empty histograms
                if not self.histograms[metric_key]:
                    del self.histograms[metric_key]
        
        self.last_cleanup = current_time

# Global metrics instance
_global_metrics = None

def get_metrics_collector(service_name: str = "default") -> MetricsCollector:
    """Get or create global metrics collector"""
    global _global_metrics
    if _global_metrics is None:
        _global_metrics = MetricsCollector(service_name)
    return _global_metrics

# Context manager for timing operations
class timer:
    """Context manager for timing operations"""
    
    def __init__(self, metrics: MetricsCollector, name: str, labels: Optional[Dict[str, str]] = None):
        self.metrics = metrics
        self.name = name
        self.labels = labels
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.metrics.record_timer(self.name, duration, self.labels)