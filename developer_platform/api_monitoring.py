"""
API Monitoring and Analytics System

Tracks API usage, performance metrics, and provides detailed analytics
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta, date
from enum import Enum
from pydantic import BaseModel, Field
import statistics
from collections import defaultdict, Counter
import json

class MetricType(str, Enum):
    """Types of metrics tracked"""
    REQUEST_COUNT = "request_count"
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    ACTIVE_USERS = "active_users"
    API_CALLS = "api_calls"
    DATA_TRANSFER = "data_transfer"
    RATE_LIMIT_HITS = "rate_limit_hits"

class TimeGranularity(str, Enum):
    """Time granularity for metrics"""
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"

class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class APIMetric(BaseModel):
    """Individual API metric"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metric_type: MetricType
    value: float
    
    # Dimensions
    api_key_id: Optional[str]
    endpoint: Optional[str]
    method: Optional[str]
    status_code: Optional[int]
    error_type: Optional[str]
    
    # Additional metadata
    organization_id: Optional[str]
    user_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    country: Optional[str]
    
    # Performance metrics
    response_time_ms: Optional[float]
    request_size_bytes: Optional[int]
    response_size_bytes: Optional[int]

class UsageQuota(BaseModel):
    """API usage quota definition"""
    organization_id: str
    quota_type: str  # requests, data_transfer, processing_hours
    limit: float
    period: str  # daily, monthly
    current_usage: float = 0
    reset_at: datetime
    
    @property
    def usage_percentage(self) -> float:
        """Calculate usage percentage"""
        return (self.current_usage / self.limit * 100) if self.limit > 0 else 0
    
    @property
    def remaining(self) -> float:
        """Calculate remaining quota"""
        return max(0, self.limit - self.current_usage)

class PerformanceMetrics(BaseModel):
    """API performance metrics summary"""
    period_start: datetime
    period_end: datetime
    
    # Request metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    
    # Performance metrics
    avg_response_time_ms: float = 0
    p50_response_time_ms: float = 0
    p95_response_time_ms: float = 0
    p99_response_time_ms: float = 0
    max_response_time_ms: float = 0
    
    # Error metrics
    error_rate: float = 0
    error_breakdown: Dict[str, int] = Field(default_factory=dict)
    
    # Throughput
    requests_per_second: float = 0
    data_transfer_mb: float = 0
    
    # Availability
    uptime_percentage: float = 100.0
    downtime_minutes: float = 0

class Alert(BaseModel):
    """System alert"""
    alert_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    severity: AlertSeverity
    alert_type: str
    message: str
    
    # Alert context
    metric_name: Optional[str]
    current_value: Optional[float]
    threshold_value: Optional[float]
    
    # Affected resources
    organization_id: Optional[str]
    api_key_id: Optional[str]
    endpoint: Optional[str]
    
    # Alert state
    is_active: bool = True
    acknowledged: bool = False
    acknowledged_by: Optional[str]
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]

class AlertRule(BaseModel):
    """Alert rule configuration"""
    rule_id: str
    name: str
    description: str
    is_enabled: bool = True
    
    # Condition
    metric_type: MetricType
    condition: str  # gt, lt, eq, gte, lte
    threshold: float
    evaluation_period_minutes: int = 5
    
    # Alert configuration
    severity: AlertSeverity
    notification_channels: List[str] = []  # email, slack, webhook
    
    # Filters
    endpoint_filter: Optional[str]
    organization_filter: Optional[str]

class APIMonitor:
    """Main API monitoring system"""
    
    def __init__(self):
        self.metrics: List[APIMetric] = []
        self.quotas: Dict[str, UsageQuota] = {}
        self.alerts: List[Alert] = []
        self.alert_rules: List[AlertRule] = []
        
        # Real-time counters
        self.request_counter = defaultdict(int)
        self.error_counter = defaultdict(int)
        self.active_connections = defaultdict(set)
        
        # Performance tracking
        self.response_times: Dict[str, List[float]] = defaultdict(list)
        
    def record_request(
        self,
        api_key_id: str,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
        request_size: int = 0,
        response_size: int = 0,
        error_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record API request metric"""
        metric = APIMetric(
            metric_type=MetricType.API_CALLS,
            value=1,
            api_key_id=api_key_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            error_type=error_type,
            response_time_ms=response_time_ms,
            request_size_bytes=request_size,
            response_size_bytes=response_size
        )
        
        if metadata:
            metric.organization_id = metadata.get("organization_id")
            metric.user_id = metadata.get("user_id")
            metric.ip_address = metadata.get("ip_address")
            metric.user_agent = metadata.get("user_agent")
            metric.country = metadata.get("country")
        
        self.metrics.append(metric)
        
        # Update real-time counters
        self.request_counter[endpoint] += 1
        if status_code >= 400:
            self.error_counter[endpoint] += 1
        
        # Track response times
        self.response_times[endpoint].append(response_time_ms)
        
        # Check quotas
        if metric.organization_id:
            self._check_quotas(metric.organization_id, endpoint)
        
        # Evaluate alert rules
        self._evaluate_alerts(metric)
    
    def get_performance_metrics(
        self,
        start_time: datetime,
        end_time: datetime,
        endpoint: Optional[str] = None,
        organization_id: Optional[str] = None
    ) -> PerformanceMetrics:
        """Calculate performance metrics for time period"""
        # Filter metrics
        filtered_metrics = [
            m for m in self.metrics
            if start_time <= m.timestamp <= end_time
            and (endpoint is None or m.endpoint == endpoint)
            and (organization_id is None or m.organization_id == organization_id)
        ]
        
        if not filtered_metrics:
            return PerformanceMetrics(
                period_start=start_time,
                period_end=end_time
            )
        
        # Calculate metrics
        total_requests = len(filtered_metrics)
        successful_requests = len([m for m in filtered_metrics if m.status_code < 400])
        failed_requests = total_requests - successful_requests
        
        # Response times
        response_times = [m.response_time_ms for m in filtered_metrics if m.response_time_ms]
        
        # Error breakdown
        error_breakdown = Counter()
        for m in filtered_metrics:
            if m.status_code >= 400:
                error_breakdown[f"{m.status_code}"] += 1
        
        # Data transfer
        data_transfer = sum(
            (m.request_size_bytes or 0) + (m.response_size_bytes or 0)
            for m in filtered_metrics
        ) / 1024 / 1024  # Convert to MB
        
        # Calculate period duration in seconds
        period_seconds = (end_time - start_time).total_seconds()
        
        return PerformanceMetrics(
            period_start=start_time,
            period_end=end_time,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time_ms=statistics.mean(response_times) if response_times else 0,
            p50_response_time_ms=statistics.median(response_times) if response_times else 0,
            p95_response_time_ms=self._percentile(response_times, 95) if response_times else 0,
            p99_response_time_ms=self._percentile(response_times, 99) if response_times else 0,
            max_response_time_ms=max(response_times) if response_times else 0,
            error_rate=(failed_requests / total_requests * 100) if total_requests > 0 else 0,
            error_breakdown=dict(error_breakdown),
            requests_per_second=total_requests / period_seconds if period_seconds > 0 else 0,
            data_transfer_mb=data_transfer
        )
    
    def get_usage_analytics(
        self,
        organization_id: str,
        start_date: date,
        end_date: date,
        granularity: TimeGranularity = TimeGranularity.DAY
    ) -> Dict[str, Any]:
        """Get detailed usage analytics"""
        start_time = datetime.combine(start_date, datetime.min.time())
        end_time = datetime.combine(end_date, datetime.max.time())
        
        # Filter metrics
        org_metrics = [
            m for m in self.metrics
            if m.organization_id == organization_id
            and start_time <= m.timestamp <= end_time
        ]
        
        # Time series data
        time_series = self._generate_time_series(
            org_metrics,
            start_time,
            end_time,
            granularity
        )
        
        # Endpoint breakdown
        endpoint_usage = Counter()
        endpoint_errors = Counter()
        endpoint_response_times = defaultdict(list)
        
        for metric in org_metrics:
            endpoint_usage[metric.endpoint] += 1
            if metric.status_code >= 400:
                endpoint_errors[metric.endpoint] += 1
            if metric.response_time_ms:
                endpoint_response_times[metric.endpoint].append(metric.response_time_ms)
        
        # Calculate endpoint statistics
        endpoint_stats = {}
        for endpoint, count in endpoint_usage.items():
            response_times = endpoint_response_times[endpoint]
            endpoint_stats[endpoint] = {
                "total_requests": count,
                "error_count": endpoint_errors[endpoint],
                "error_rate": (endpoint_errors[endpoint] / count * 100) if count > 0 else 0,
                "avg_response_time": statistics.mean(response_times) if response_times else 0,
                "p95_response_time": self._percentile(response_times, 95) if response_times else 0
            }
        
        # User analytics
        unique_users = set(m.user_id for m in org_metrics if m.user_id)
        daily_active_users = self._calculate_daily_active_users(org_metrics)
        
        # Geographic distribution
        country_distribution = Counter(
            m.country for m in org_metrics if m.country
        )
        
        # API key usage
        api_key_usage = Counter(m.api_key_id for m in org_metrics)
        
        # Cost estimation (simplified)
        total_requests = len(org_metrics)
        total_data_gb = sum(
            (m.request_size_bytes or 0) + (m.response_size_bytes or 0)
            for m in org_metrics
        ) / 1024 / 1024 / 1024
        
        estimated_cost = (total_requests * 0.0001) + (total_data_gb * 0.09)  # Example pricing
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "summary": {
                "total_requests": total_requests,
                "unique_users": len(unique_users),
                "total_data_gb": round(total_data_gb, 2),
                "estimated_cost": round(estimated_cost, 2),
                "avg_daily_requests": total_requests / ((end_date - start_date).days + 1)
            },
            "time_series": time_series,
            "endpoint_statistics": endpoint_stats,
            "daily_active_users": daily_active_users,
            "geographic_distribution": dict(country_distribution.most_common(10)),
            "top_api_keys": [
                {"api_key_id": key, "requests": count}
                for key, count in api_key_usage.most_common(10)
            ],
            "performance": self.get_performance_metrics(start_time, end_time, organization_id=organization_id)
        }
    
    def set_quota(
        self,
        organization_id: str,
        quota_type: str,
        limit: float,
        period: str = "monthly"
    ):
        """Set usage quota for organization"""
        reset_at = self._calculate_quota_reset(period)
        
        quota = UsageQuota(
            organization_id=organization_id,
            quota_type=quota_type,
            limit=limit,
            period=period,
            reset_at=reset_at
        )
        
        key = f"{organization_id}:{quota_type}"
        self.quotas[key] = quota
    
    def check_quota_status(
        self,
        organization_id: str,
        quota_type: str
    ) -> Optional[UsageQuota]:
        """Check current quota status"""
        key = f"{organization_id}:{quota_type}"
        quota = self.quotas.get(key)
        
        if quota and datetime.utcnow() > quota.reset_at:
            # Reset quota
            quota.current_usage = 0
            quota.reset_at = self._calculate_quota_reset(quota.period)
        
        return quota
    
    def create_alert_rule(
        self,
        name: str,
        metric_type: MetricType,
        condition: str,
        threshold: float,
        severity: AlertSeverity = AlertSeverity.WARNING,
        endpoint_filter: Optional[str] = None
    ) -> AlertRule:
        """Create new alert rule"""
        rule = AlertRule(
            rule_id=f"rule_{len(self.alert_rules) + 1}",
            name=name,
            description=f"Alert when {metric_type.value} {condition} {threshold}",
            metric_type=metric_type,
            condition=condition,
            threshold=threshold,
            severity=severity,
            endpoint_filter=endpoint_filter
        )
        
        self.alert_rules.append(rule)
        return rule
    
    def get_active_alerts(
        self,
        organization_id: Optional[str] = None,
        severity: Optional[AlertSeverity] = None
    ) -> List[Alert]:
        """Get active alerts"""
        alerts = [a for a in self.alerts if a.is_active]
        
        if organization_id:
            alerts = [a for a in alerts if a.organization_id == organization_id]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return sorted(alerts, key=lambda a: a.created_at, reverse=True)
    
    def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str
    ) -> bool:
        """Acknowledge an alert"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                alert.acknowledged_by = acknowledged_by
                alert.acknowledged_at = datetime.utcnow()
                return True
        return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status"""
        now = datetime.utcnow()
        last_hour = now - timedelta(hours=1)
        
        # Recent metrics
        recent_metrics = [
            m for m in self.metrics
            if m.timestamp >= last_hour
        ]
        
        if not recent_metrics:
            return {
                "status": "unknown",
                "message": "No recent data"
            }
        
        # Calculate health indicators
        error_rate = len([m for m in recent_metrics if m.status_code >= 500]) / len(recent_metrics) * 100
        avg_response_time = statistics.mean([m.response_time_ms for m in recent_metrics if m.response_time_ms] or [0])
        
        # Active alerts
        critical_alerts = len([a for a in self.alerts if a.is_active and a.severity == AlertSeverity.CRITICAL])
        warning_alerts = len([a for a in self.alerts if a.is_active and a.severity == AlertSeverity.WARNING])
        
        # Determine status
        if critical_alerts > 0 or error_rate > 10:
            status = "critical"
            message = "System experiencing critical issues"
        elif warning_alerts > 0 or error_rate > 5 or avg_response_time > 1000:
            status = "warning"
            message = "System experiencing degraded performance"
        else:
            status = "healthy"
            message = "All systems operational"
        
        return {
            "status": status,
            "message": message,
            "indicators": {
                "error_rate": round(error_rate, 2),
                "avg_response_time_ms": round(avg_response_time, 2),
                "requests_per_minute": len(recent_metrics) / 60,
                "active_endpoints": len(set(m.endpoint for m in recent_metrics))
            },
            "alerts": {
                "critical": critical_alerts,
                "warning": warning_alerts,
                "total_active": len([a for a in self.alerts if a.is_active])
            },
            "last_check": now.isoformat()
        }
    
    def generate_sla_report(
        self,
        organization_id: str,
        month: int,
        year: int
    ) -> Dict[str, Any]:
        """Generate SLA compliance report"""
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(seconds=1)
        
        # Get metrics for the month
        month_metrics = [
            m for m in self.metrics
            if m.organization_id == organization_id
            and start_date <= m.timestamp <= end_date
        ]
        
        if not month_metrics:
            return {
                "error": "No data available for specified period"
            }
        
        # Calculate SLA metrics
        total_requests = len(month_metrics)
        successful_requests = len([m for m in month_metrics if m.status_code < 500])
        
        # Uptime calculation (simplified)
        uptime_percentage = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        
        # Response time SLA (e.g., 95% of requests under 1000ms)
        response_times = [m.response_time_ms for m in month_metrics if m.response_time_ms]
        under_sla = len([rt for rt in response_times if rt < 1000])
        response_time_sla = (under_sla / len(response_times) * 100) if response_times else 0
        
        # Error rate
        error_rate = ((total_requests - successful_requests) / total_requests * 100) if total_requests > 0 else 0
        
        # Daily breakdown
        daily_stats = defaultdict(lambda: {"requests": 0, "errors": 0, "total_response_time": 0})
        
        for metric in month_metrics:
            day = metric.timestamp.date()
            daily_stats[day]["requests"] += 1
            if metric.status_code >= 500:
                daily_stats[day]["errors"] += 1
            if metric.response_time_ms:
                daily_stats[day]["total_response_time"] += metric.response_time_ms
        
        daily_breakdown = []
        for day, stats in sorted(daily_stats.items()):
            daily_breakdown.append({
                "date": day.isoformat(),
                "requests": stats["requests"],
                "error_rate": (stats["errors"] / stats["requests"] * 100) if stats["requests"] > 0 else 0,
                "avg_response_time": stats["total_response_time"] / stats["requests"] if stats["requests"] > 0 else 0
            })
        
        return {
            "organization_id": organization_id,
            "period": {
                "month": month,
                "year": year,
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "sla_metrics": {
                "uptime_percentage": round(uptime_percentage, 3),
                "uptime_sla_target": 99.9,
                "uptime_sla_met": uptime_percentage >= 99.9,
                "response_time_sla_percentage": round(response_time_sla, 2),
                "response_time_sla_target": 95.0,
                "response_time_sla_met": response_time_sla >= 95.0,
                "error_rate": round(error_rate, 3),
                "error_rate_sla_target": 0.1,
                "error_rate_sla_met": error_rate <= 0.1
            },
            "summary": {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": total_requests - successful_requests,
                "avg_response_time": round(statistics.mean(response_times), 2) if response_times else 0,
                "p95_response_time": round(self._percentile(response_times, 95), 2) if response_times else 0,
                "p99_response_time": round(self._percentile(response_times, 99), 2) if response_times else 0
            },
            "daily_breakdown": daily_breakdown,
            "sla_credits": self._calculate_sla_credits(uptime_percentage)
        }
    
    def _check_quotas(self, organization_id: str, endpoint: str):
        """Check and update quotas"""
        # Check request quota
        request_quota_key = f"{organization_id}:requests"
        if request_quota_key in self.quotas:
            quota = self.quotas[request_quota_key]
            quota.current_usage += 1
            
            # Alert on quota thresholds
            if quota.usage_percentage >= 80 and quota.usage_percentage < 90:
                self._create_quota_alert(quota, AlertSeverity.WARNING, 80)
            elif quota.usage_percentage >= 90 and quota.usage_percentage < 100:
                self._create_quota_alert(quota, AlertSeverity.ERROR, 90)
            elif quota.usage_percentage >= 100:
                self._create_quota_alert(quota, AlertSeverity.CRITICAL, 100)
    
    def _evaluate_alerts(self, metric: APIMetric):
        """Evaluate alert rules against new metric"""
        for rule in self.alert_rules:
            if not rule.is_enabled:
                continue
            
            # Check filters
            if rule.endpoint_filter and metric.endpoint != rule.endpoint_filter:
                continue
            
            if rule.organization_filter and metric.organization_id != rule.organization_filter:
                continue
            
            # Evaluate condition
            should_alert = False
            current_value = None
            
            if rule.metric_type == MetricType.RESPONSE_TIME:
                current_value = metric.response_time_ms
                should_alert = self._evaluate_condition(
                    current_value,
                    rule.condition,
                    rule.threshold
                )
            
            elif rule.metric_type == MetricType.ERROR_RATE:
                # Calculate error rate for endpoint
                recent_metrics = [
                    m for m in self.metrics[-100:]  # Last 100 requests
                    if m.endpoint == metric.endpoint
                ]
                if recent_metrics:
                    error_count = len([m for m in recent_metrics if m.status_code >= 400])
                    current_value = (error_count / len(recent_metrics) * 100)
                    should_alert = self._evaluate_condition(
                        current_value,
                        rule.condition,
                        rule.threshold
                    )
            
            if should_alert and current_value is not None:
                self._create_alert(rule, metric, current_value)
    
    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Evaluate alert condition"""
        if condition == "gt":
            return value > threshold
        elif condition == "lt":
            return value < threshold
        elif condition == "gte":
            return value >= threshold
        elif condition == "lte":
            return value <= threshold
        elif condition == "eq":
            return value == threshold
        return False
    
    def _create_alert(self, rule: AlertRule, metric: APIMetric, current_value: float):
        """Create new alert"""
        alert = Alert(
            alert_id=f"alert_{len(self.alerts) + 1}",
            severity=rule.severity,
            alert_type=f"{rule.metric_type.value}_threshold",
            message=f"{rule.name}: {rule.metric_type.value} is {current_value} (threshold: {rule.threshold})",
            metric_name=rule.metric_type.value,
            current_value=current_value,
            threshold_value=rule.threshold,
            organization_id=metric.organization_id,
            api_key_id=metric.api_key_id,
            endpoint=metric.endpoint
        )
        
        self.alerts.append(alert)
        
        # TODO: Send notifications via configured channels
    
    def _create_quota_alert(self, quota: UsageQuota, severity: AlertSeverity, threshold: int):
        """Create quota alert"""
        # Check if similar alert already exists
        existing_alert = next(
            (a for a in self.alerts
             if a.is_active
             and a.organization_id == quota.organization_id
             and a.alert_type == "quota_threshold"
             and a.threshold_value == threshold),
            None
        )
        
        if not existing_alert:
            alert = Alert(
                alert_id=f"alert_{len(self.alerts) + 1}",
                severity=severity,
                alert_type="quota_threshold",
                message=f"Usage quota {quota.quota_type} at {quota.usage_percentage:.1f}% (threshold: {threshold}%)",
                metric_name="quota_usage",
                current_value=quota.usage_percentage,
                threshold_value=threshold,
                organization_id=quota.organization_id
            )
            
            self.alerts.append(alert)
    
    def _generate_time_series(
        self,
        metrics: List[APIMetric],
        start_time: datetime,
        end_time: datetime,
        granularity: TimeGranularity
    ) -> List[Dict[str, Any]]:
        """Generate time series data"""
        # Determine time buckets
        buckets = []
        current = start_time
        
        if granularity == TimeGranularity.HOUR:
            delta = timedelta(hours=1)
        elif granularity == TimeGranularity.DAY:
            delta = timedelta(days=1)
        elif granularity == TimeGranularity.WEEK:
            delta = timedelta(weeks=1)
        else:
            delta = timedelta(days=1)
        
        while current <= end_time:
            bucket_end = current + delta
            
            # Filter metrics for this bucket
            bucket_metrics = [
                m for m in metrics
                if current <= m.timestamp < bucket_end
            ]
            
            # Calculate bucket statistics
            bucket_data = {
                "timestamp": current.isoformat(),
                "requests": len(bucket_metrics),
                "errors": len([m for m in bucket_metrics if m.status_code >= 400]),
                "avg_response_time": 0,
                "data_transfer_mb": 0
            }
            
            if bucket_metrics:
                response_times = [m.response_time_ms for m in bucket_metrics if m.response_time_ms]
                if response_times:
                    bucket_data["avg_response_time"] = round(statistics.mean(response_times), 2)
                
                bucket_data["data_transfer_mb"] = round(
                    sum(
                        (m.request_size_bytes or 0) + (m.response_size_bytes or 0)
                        for m in bucket_metrics
                    ) / 1024 / 1024,
                    2
                )
            
            buckets.append(bucket_data)
            current = bucket_end
        
        return buckets
    
    def _calculate_daily_active_users(self, metrics: List[APIMetric]) -> Dict[str, int]:
        """Calculate daily active users"""
        daily_users = defaultdict(set)
        
        for metric in metrics:
            if metric.user_id:
                day = metric.timestamp.date().isoformat()
                daily_users[day].add(metric.user_id)
        
        return {day: len(users) for day, users in daily_users.items()}
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile value"""
        if not values:
            return 0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * (percentile / 100))
        
        if index >= len(sorted_values):
            return sorted_values[-1]
        
        return sorted_values[index]
    
    def _calculate_quota_reset(self, period: str) -> datetime:
        """Calculate next quota reset time"""
        now = datetime.utcnow()
        
        if period == "daily":
            # Reset at midnight UTC
            return datetime.combine(
                now.date() + timedelta(days=1),
                datetime.min.time()
            )
        elif period == "monthly":
            # Reset on first day of next month
            if now.month == 12:
                return datetime(now.year + 1, 1, 1)
            else:
                return datetime(now.year, now.month + 1, 1)
        
        return now + timedelta(days=30)  # Default 30 days
    
    def _calculate_sla_credits(self, uptime_percentage: float) -> Dict[str, Any]:
        """Calculate SLA credits based on uptime"""
        # Example SLA credit structure
        if uptime_percentage >= 99.9:
            return {"percentage": 0, "description": "No credits - SLA met"}
        elif uptime_percentage >= 99.0:
            return {"percentage": 10, "description": "10% credit"}
        elif uptime_percentage >= 95.0:
            return {"percentage": 25, "description": "25% credit"}
        else:
            return {"percentage": 100, "description": "100% credit"}

# Example usage
if __name__ == "__main__":
    # Initialize monitor
    monitor = APIMonitor()
    
    # Set quotas
    monitor.set_quota("org_123", "requests", 10000, "monthly")
    monitor.set_quota("org_123", "data_transfer", 100, "monthly")  # 100 GB
    
    # Create alert rules
    monitor.create_alert_rule(
        name="High Response Time",
        metric_type=MetricType.RESPONSE_TIME,
        condition="gt",
        threshold=1000,  # 1 second
        severity=AlertSeverity.WARNING
    )
    
    monitor.create_alert_rule(
        name="High Error Rate",
        metric_type=MetricType.ERROR_RATE,
        condition="gt",
        threshold=5,  # 5%
        severity=AlertSeverity.ERROR
    )
    
    # Simulate API requests
    import random
    
    for i in range(100):
        monitor.record_request(
            api_key_id=f"key_{random.randint(1, 5)}",
            endpoint="/api/v1/transcriptions",
            method="POST",
            status_code=random.choice([200, 200, 200, 400, 500]),
            response_time_ms=random.uniform(50, 500),
            request_size=random.randint(1000, 10000),
            response_size=random.randint(5000, 50000),
            metadata={
                "organization_id": "org_123",
                "user_id": f"user_{random.randint(1, 10)}",
                "country": random.choice(["US", "UK", "CA", "AU"])
            }
        )
    
    # Get performance metrics
    now = datetime.utcnow()
    metrics = monitor.get_performance_metrics(
        now - timedelta(hours=1),
        now
    )
    
    print(f"Performance Metrics:")
    print(f"  Total Requests: {metrics.total_requests}")
    print(f"  Error Rate: {metrics.error_rate:.2f}%")
    print(f"  Avg Response Time: {metrics.avg_response_time_ms:.2f}ms")
    print(f"  P95 Response Time: {metrics.p95_response_time_ms:.2f}ms")
    
    # Get health status
    health = monitor.get_health_status()
    print(f"\nHealth Status: {health['status']}")
    print(f"Message: {health['message']}")
    
    # Check quotas
    quota = monitor.check_quota_status("org_123", "requests")
    if quota:
        print(f"\nQuota Status:")
        print(f"  Usage: {quota.current_usage}/{quota.limit}")
        print(f"  Percentage: {quota.usage_percentage:.1f}%")
    
    # Get active alerts
    alerts = monitor.get_active_alerts()
    print(f"\nActive Alerts: {len(alerts)}")
    for alert in alerts[:5]:
        print(f"  - [{alert.severity.value.upper()}] {alert.message}")