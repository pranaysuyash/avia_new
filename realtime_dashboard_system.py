"""
Real-time Dashboard System
Provides live updates, metrics, and visualizations for all platform activities
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Any, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum
import redis.asyncio as redis
from fastapi import WebSocket, WebSocketDisconnect, HTTPException
import numpy as np
import pandas as pd
from collections import defaultdict, deque
import logging
import heapq
import statistics

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    RATE = "rate"
    PERCENTAGE = "percentage"

class UpdatePriority(Enum):
    """Update priority levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

@dataclass
class Metric:
    """Represents a dashboard metric"""
    id: str
    name: str
    type: MetricType
    value: float
    unit: str
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    history: deque = field(default_factory=lambda: deque(maxlen=100))
    
    def update(self, value: float, timestamp: Optional[datetime] = None):
        """Update metric value"""
        self.value = value
        self.timestamp = timestamp or datetime.utcnow()
        self.history.append((self.timestamp, value))
        
    def get_average(self, window_seconds: int = 60) -> float:
        """Get average value over time window"""
        if not self.history:
            return 0
            
        cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
        values = [v for t, v in self.history if t > cutoff]
        return statistics.mean(values) if values else 0
        
    def get_rate(self, window_seconds: int = 60) -> float:
        """Get rate of change"""
        if len(self.history) < 2:
            return 0
            
        cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
        values = [(t, v) for t, v in self.history if t > cutoff]
        
        if len(values) < 2:
            return 0
            
        time_diff = (values[-1][0] - values[0][0]).total_seconds()
        value_diff = values[-1][1] - values[0][1]
        
        return value_diff / time_diff if time_diff > 0 else 0
        
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type.value,
            'value': self.value,
            'unit': self.unit,
            'timestamp': self.timestamp.isoformat(),
            'tags': self.tags,
            'metadata': self.metadata,
            'average': self.get_average(),
            'rate': self.get_rate()
        }

@dataclass
class Alert:
    """Represents a dashboard alert"""
    id: str
    name: str
    severity: str  # critical, warning, info
    message: str
    metric_id: Optional[str]
    condition: str
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    actions: List[str] = field(default_factory=list)
    
    def resolve(self):
        """Resolve the alert"""
        self.resolved_at = datetime.utcnow()
        
    def acknowledge(self, user_id: str):
        """Acknowledge the alert"""
        self.acknowledged = True
        self.acknowledged_by = user_id
        
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'severity': self.severity,
            'message': self.message,
            'metric_id': self.metric_id,
            'condition': self.condition,
            'triggered_at': self.triggered_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'acknowledged': self.acknowledged,
            'acknowledged_by': self.acknowledged_by,
            'actions': self.actions
        }

@dataclass
class Widget:
    """Represents a dashboard widget"""
    id: str
    type: str  # chart, gauge, number, table, map, etc.
    title: str
    position: Dict[str, int]  # x, y, width, height
    config: Dict[str, Any]
    metric_ids: List[str]
    refresh_interval: int = 5  # seconds
    last_update: datetime = field(default_factory=datetime.utcnow)
    
    def should_refresh(self) -> bool:
        """Check if widget should refresh"""
        return (datetime.utcnow() - self.last_update).total_seconds() > self.refresh_interval

@dataclass
class Dashboard:
    """Represents a dashboard"""
    id: str
    name: str
    user_id: str
    widgets: List[Widget]
    layout: str  # grid, flex, fixed
    theme: str  # light, dark, auto
    created_at: datetime
    updated_at: datetime
    is_public: bool = False
    shared_with: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

class RealtimeDashboardSystem:
    """Main system for real-time dashboards"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.metrics: Dict[str, Metric] = {}
        self.alerts: Dict[str, Alert] = {}
        self.dashboards: Dict[str, Dashboard] = {}
        self.websockets: Dict[str, Set[WebSocket]] = defaultdict(set)
        self.subscriptions: Dict[str, Set[str]] = defaultdict(set)  # user_id -> dashboard_ids
        self.update_queue: List[Tuple[int, datetime, Dict]] = []  # Priority queue
        self._running = False
        self._broadcast_task = None
        self._aggregation_task = None
        
        # Performance metrics
        self.performance_metrics = {
            'updates_sent': 0,
            'websocket_connections': 0,
            'active_dashboards': 0,
            'metrics_tracked': 0
        }
        
    async def initialize(self):
        """Initialize the dashboard system"""
        if not self.redis_client:
            self.redis_client = await redis.from_url("redis://localhost:6379")
            
        self._running = True
        self._broadcast_task = asyncio.create_task(self._broadcast_updates())
        self._aggregation_task = asyncio.create_task(self._aggregate_metrics())
        
        # Initialize default metrics
        await self._initialize_default_metrics()
        
        logger.info("Real-time dashboard system initialized")
        
    async def shutdown(self):
        """Shutdown the dashboard system"""
        self._running = False
        
        if self._broadcast_task:
            self._broadcast_task.cancel()
        if self._aggregation_task:
            self._aggregation_task.cancel()
            
        # Close all WebSocket connections
        for dashboard_id in self.websockets:
            for ws in self.websockets[dashboard_id]:
                await ws.close()
                
        if self.redis_client:
            await self.redis_client.close()
            
        logger.info("Real-time dashboard system shutdown")
        
    async def _initialize_default_metrics(self):
        """Initialize default system metrics"""
        default_metrics = [
            Metric(
                id="system.cpu",
                name="CPU Usage",
                type=MetricType.PERCENTAGE,
                value=0,
                unit="%"
            ),
            Metric(
                id="system.memory",
                name="Memory Usage",
                type=MetricType.PERCENTAGE,
                value=0,
                unit="%"
            ),
            Metric(
                id="transcription.active",
                name="Active Transcriptions",
                type=MetricType.GAUGE,
                value=0,
                unit="sessions"
            ),
            Metric(
                id="transcription.rate",
                name="Transcription Rate",
                type=MetricType.RATE,
                value=0,
                unit="words/min"
            ),
            Metric(
                id="collaboration.users",
                name="Active Collaborators",
                type=MetricType.GAUGE,
                value=0,
                unit="users"
            ),
            Metric(
                id="api.requests",
                name="API Requests",
                type=MetricType.COUNTER,
                value=0,
                unit="requests"
            ),
            Metric(
                id="api.latency",
                name="API Latency",
                type=MetricType.HISTOGRAM,
                value=0,
                unit="ms"
            ),
            Metric(
                id="storage.usage",
                name="Storage Usage",
                type=MetricType.GAUGE,
                value=0,
                unit="GB"
            )
        ]
        
        for metric in default_metrics:
            self.metrics[metric.id] = metric
            
    async def create_dashboard(
        self,
        name: str,
        user_id: str,
        layout: str = "grid"
    ) -> str:
        """Create a new dashboard"""
        dashboard_id = str(uuid.uuid4())
        
        dashboard = Dashboard(
            id=dashboard_id,
            name=name,
            user_id=user_id,
            widgets=[],
            layout=layout,
            theme="auto",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.dashboards[dashboard_id] = dashboard
        
        # Store in Redis
        if self.redis_client:
            await self.redis_client.hset(
                f"dashboard:{dashboard_id}",
                mapping={
                    'name': name,
                    'user_id': user_id,
                    'layout': layout,
                    'created_at': dashboard.created_at.isoformat()
                }
            )
            
        logger.info(f"Created dashboard {dashboard_id}")
        return dashboard_id
        
    async def add_widget(
        self,
        dashboard_id: str,
        widget_type: str,
        title: str,
        position: Dict[str, int],
        metric_ids: List[str],
        config: Optional[Dict] = None
    ) -> str:
        """Add widget to dashboard"""
        if dashboard_id not in self.dashboards:
            raise ValueError(f"Dashboard {dashboard_id} not found")
            
        widget_id = str(uuid.uuid4())
        
        widget = Widget(
            id=widget_id,
            type=widget_type,
            title=title,
            position=position,
            config=config or {},
            metric_ids=metric_ids
        )
        
        self.dashboards[dashboard_id].widgets.append(widget)
        self.dashboards[dashboard_id].updated_at = datetime.utcnow()
        
        # Notify subscribers
        await self._notify_dashboard_update(dashboard_id, {
            'action': 'widget_added',
            'widget': asdict(widget)
        })
        
        logger.info(f"Added widget {widget_id} to dashboard {dashboard_id}")
        return widget_id
        
    async def update_metric(
        self,
        metric_id: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
        priority: UpdatePriority = UpdatePriority.MEDIUM
    ):
        """Update metric value"""
        if metric_id not in self.metrics:
            # Create new metric if doesn't exist
            self.metrics[metric_id] = Metric(
                id=metric_id,
                name=metric_id,
                type=MetricType.GAUGE,
                value=value,
                unit="",
                timestamp=datetime.utcnow(),
                tags=tags or {}
            )
        else:
            self.metrics[metric_id].update(value)
            if tags:
                self.metrics[metric_id].tags.update(tags)
                
        # Add to update queue
        update = {
            'metric_id': metric_id,
            'value': value,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        heapq.heappush(
            self.update_queue,
            (priority.value, datetime.utcnow(), update)
        )
        
        # Check for alerts
        await self._check_alerts(metric_id, value)
        
        # Update performance metrics
        self.performance_metrics['metrics_tracked'] = len(self.metrics)
        
    async def create_alert(
        self,
        name: str,
        metric_id: str,
        condition: str,
        severity: str = "warning",
        actions: Optional[List[str]] = None
    ) -> str:
        """Create an alert rule"""
        alert_id = str(uuid.uuid4())
        
        # Store alert configuration
        if self.redis_client:
            await self.redis_client.hset(
                f"alert:config:{alert_id}",
                mapping={
                    'name': name,
                    'metric_id': metric_id,
                    'condition': condition,
                    'severity': severity,
                    'actions': json.dumps(actions or [])
                }
            )
            
        logger.info(f"Created alert {alert_id}")
        return alert_id
        
    async def _check_alerts(self, metric_id: str, value: float):
        """Check if any alerts should be triggered"""
        # Get alert configurations from Redis
        if not self.redis_client:
            return
            
        alert_configs = await self.redis_client.keys(f"alert:config:*")
        
        for config_key in alert_configs:
            config = await self.redis_client.hgetall(config_key)
            
            if config.get(b'metric_id', b'').decode() != metric_id:
                continue
                
            condition = config.get(b'condition', b'').decode()
            
            # Evaluate condition (simplified)
            triggered = False
            if '>' in condition:
                threshold = float(condition.split('>')[-1].strip())
                triggered = value > threshold
            elif '<' in condition:
                threshold = float(condition.split('<')[-1].strip())
                triggered = value < threshold
                
            if triggered:
                alert_id = str(uuid.uuid4())
                alert = Alert(
                    id=alert_id,
                    name=config.get(b'name', b'').decode(),
                    severity=config.get(b'severity', b'warning').decode(),
                    message=f"Metric {metric_id} = {value} {condition}",
                    metric_id=metric_id,
                    condition=condition,
                    triggered_at=datetime.utcnow()
                )
                
                self.alerts[alert_id] = alert
                
                # Notify all dashboards
                await self._broadcast_alert(alert)
                
    async def handle_websocket(
        self,
        websocket: WebSocket,
        dashboard_id: str,
        user_id: str
    ):
        """Handle WebSocket connection for dashboard"""
        await websocket.accept()
        self.websockets[dashboard_id].add(websocket)
        self.subscriptions[user_id].add(dashboard_id)
        self.performance_metrics['websocket_connections'] += 1
        self.performance_metrics['active_dashboards'] = len(self.dashboards)
        
        try:
            # Send initial dashboard state
            await self._send_dashboard_state(websocket, dashboard_id)
            
            while True:
                # Receive control messages
                data = await websocket.receive_json()
                await self._handle_dashboard_message(dashboard_id, user_id, data)
                
        except WebSocketDisconnect:
            logger.info(f"Dashboard {dashboard_id} disconnected")
        except Exception as e:
            logger.error(f"Dashboard WebSocket error: {e}")
        finally:
            self.websockets[dashboard_id].discard(websocket)
            self.subscriptions[user_id].discard(dashboard_id)
            self.performance_metrics['websocket_connections'] -= 1
            
    async def _handle_dashboard_message(
        self,
        dashboard_id: str,
        user_id: str,
        data: Dict
    ):
        """Handle dashboard control messages"""
        command = data.get('command')
        
        if command == 'refresh':
            await self._send_dashboard_state(
                next(iter(self.websockets[dashboard_id])),
                dashboard_id
            )
        elif command == 'acknowledge_alert':
            alert_id = data.get('alert_id')
            if alert_id in self.alerts:
                self.alerts[alert_id].acknowledge(user_id)
        elif command == 'update_widget':
            widget_id = data.get('widget_id')
            config = data.get('config')
            await self._update_widget_config(dashboard_id, widget_id, config)
        elif command == 'set_theme':
            theme = data.get('theme')
            if dashboard_id in self.dashboards:
                self.dashboards[dashboard_id].theme = theme
                
    async def _send_dashboard_state(self, websocket: WebSocket, dashboard_id: str):
        """Send current dashboard state"""
        if dashboard_id not in self.dashboards:
            return
            
        dashboard = self.dashboards[dashboard_id]
        
        # Gather widget data
        widgets_data = []
        for widget in dashboard.widgets:
            widget_data = asdict(widget)
            widget_data['metrics'] = [
                self.metrics[mid].to_dict()
                for mid in widget.metric_ids
                if mid in self.metrics
            ]
            widgets_data.append(widget_data)
            
        state = {
            'type': 'dashboard_state',
            'dashboard': {
                'id': dashboard.id,
                'name': dashboard.name,
                'layout': dashboard.layout,
                'theme': dashboard.theme,
                'widgets': widgets_data
            },
            'alerts': [
                alert.to_dict()
                for alert in self.alerts.values()
                if not alert.resolved_at
            ],
            'performance': self.performance_metrics,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            await websocket.send_json(state)
        except Exception as e:
            logger.error(f"Failed to send dashboard state: {e}")
            
    async def _broadcast_updates(self):
        """Broadcast metric updates to dashboards"""
        while self._running:
            try:
                await asyncio.sleep(0.1)  # 100ms intervals
                
                if not self.update_queue:
                    continue
                    
                # Process updates by priority
                updates_to_send = []
                current_time = datetime.utcnow()
                
                while self.update_queue and len(updates_to_send) < 50:
                    priority, timestamp, update = heapq.heappop(self.update_queue)
                    
                    # Skip old updates
                    if (current_time - timestamp).total_seconds() > 5:
                        continue
                        
                    updates_to_send.append(update)
                    
                if updates_to_send:
                    # Send to all connected dashboards
                    message = {
                        'type': 'metric_updates',
                        'updates': updates_to_send,
                        'timestamp': current_time.isoformat()
                    }
                    
                    for dashboard_id, websockets in self.websockets.items():
                        for ws in websockets:
                            try:
                                await ws.send_json(message)
                                self.performance_metrics['updates_sent'] += 1
                            except Exception as e:
                                logger.error(f"Failed to send update: {e}")
                                
            except Exception as e:
                logger.error(f"Error in broadcast task: {e}")
                
    async def _broadcast_alert(self, alert: Alert):
        """Broadcast alert to all dashboards"""
        message = {
            'type': 'alert',
            'alert': alert.to_dict(),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        for dashboard_id, websockets in self.websockets.items():
            for ws in websockets:
                try:
                    await ws.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send alert: {e}")
                    
    async def _notify_dashboard_update(self, dashboard_id: str, update: Dict):
        """Notify subscribers of dashboard update"""
        if dashboard_id not in self.websockets:
            return
            
        message = {
            'type': 'dashboard_update',
            'update': update,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        for ws in self.websockets[dashboard_id]:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send dashboard update: {e}")
                
    async def _update_widget_config(
        self,
        dashboard_id: str,
        widget_id: str,
        config: Dict
    ):
        """Update widget configuration"""
        if dashboard_id not in self.dashboards:
            return
            
        dashboard = self.dashboards[dashboard_id]
        
        for widget in dashboard.widgets:
            if widget.id == widget_id:
                widget.config.update(config)
                widget.last_update = datetime.utcnow()
                break
                
        await self._notify_dashboard_update(dashboard_id, {
            'action': 'widget_updated',
            'widget_id': widget_id,
            'config': config
        })
        
    async def _aggregate_metrics(self):
        """Aggregate metrics periodically"""
        while self._running:
            try:
                await asyncio.sleep(10)  # Every 10 seconds
                
                # Calculate aggregated metrics
                for metric_id, metric in self.metrics.items():
                    if metric.type == MetricType.RATE:
                        # Calculate rate
                        metric.value = metric.get_rate()
                    elif metric.type == MetricType.HISTOGRAM:
                        # Calculate percentiles
                        if metric.history:
                            values = [v for _, v in metric.history]
                            metric.metadata['p50'] = np.percentile(values, 50)
                            metric.metadata['p95'] = np.percentile(values, 95)
                            metric.metadata['p99'] = np.percentile(values, 99)
                            
                # Store aggregated data in Redis
                if self.redis_client:
                    for metric_id, metric in self.metrics.items():
                        await self.redis_client.hset(
                            f"metric:aggregate:{metric_id}",
                            mapping={
                                'average': metric.get_average(),
                                'rate': metric.get_rate(),
                                'timestamp': datetime.utcnow().isoformat()
                            }
                        )
                        
            except Exception as e:
                logger.error(f"Error in aggregation task: {e}")
                
    async def get_dashboard_analytics(self, dashboard_id: str) -> Dict:
        """Get analytics for a dashboard"""
        if dashboard_id not in self.dashboards:
            return {}
            
        dashboard = self.dashboards[dashboard_id]
        
        # Calculate analytics
        total_metrics = sum(len(w.metric_ids) for w in dashboard.widgets)
        active_alerts = sum(
            1 for a in self.alerts.values()
            if not a.resolved_at and any(
                a.metric_id in w.metric_ids
                for w in dashboard.widgets
            )
        )
        
        return {
            'dashboard_id': dashboard_id,
            'name': dashboard.name,
            'widget_count': len(dashboard.widgets),
            'total_metrics': total_metrics,
            'active_alerts': active_alerts,
            'created_at': dashboard.created_at.isoformat(),
            'updated_at': dashboard.updated_at.isoformat(),
            'is_public': dashboard.is_public,
            'shared_users': len(dashboard.shared_with)
        }
        
    async def export_dashboard(self, dashboard_id: str) -> Dict:
        """Export dashboard configuration"""
        if dashboard_id not in self.dashboards:
            return {}
            
        dashboard = self.dashboards[dashboard_id]
        
        return {
            'id': dashboard.id,
            'name': dashboard.name,
            'layout': dashboard.layout,
            'theme': dashboard.theme,
            'widgets': [asdict(w) for w in dashboard.widgets],
            'created_at': dashboard.created_at.isoformat(),
            'updated_at': dashboard.updated_at.isoformat()
        }

# Visualization helpers
class ChartGenerator:
    """Generates chart configurations for widgets"""
    
    @staticmethod
    def line_chart(metrics: List[Metric], config: Dict) -> Dict:
        """Generate line chart configuration"""
        series = []
        
        for metric in metrics:
            data = [
                {'x': t.isoformat(), 'y': v}
                for t, v in metric.history
            ]
            
            series.append({
                'name': metric.name,
                'data': data,
                'color': config.get('color', '#3b82f6')
            })
            
        return {
            'type': 'line',
            'series': series,
            'options': {
                'animation': config.get('animation', True),
                'smooth': config.get('smooth', True),
                'area': config.get('area', False)
            }
        }
        
    @staticmethod
    def gauge_chart(metric: Metric, config: Dict) -> Dict:
        """Generate gauge chart configuration"""
        return {
            'type': 'gauge',
            'value': metric.value,
            'min': config.get('min', 0),
            'max': config.get('max', 100),
            'thresholds': config.get('thresholds', [
                {'value': 30, 'color': 'green'},
                {'value': 60, 'color': 'yellow'},
                {'value': 90, 'color': 'red'}
            ])
        }
        
    @staticmethod
    def bar_chart(metrics: List[Metric], config: Dict) -> Dict:
        """Generate bar chart configuration"""
        return {
            'type': 'bar',
            'data': [
                {'label': m.name, 'value': m.value}
                for m in metrics
            ],
            'orientation': config.get('orientation', 'vertical'),
            'color': config.get('color', '#3b82f6')
        }

# Usage example
async def demo_dashboard():
    """Demonstrate dashboard system"""
    system = RealtimeDashboardSystem()
    await system.initialize()
    
    # Create dashboard
    dashboard_id = await system.create_dashboard(
        "Operations Dashboard",
        "user123"
    )
    
    # Add widgets
    await system.add_widget(
        dashboard_id,
        "line",
        "API Latency",
        {"x": 0, "y": 0, "width": 6, "height": 4},
        ["api.latency"]
    )
    
    await system.add_widget(
        dashboard_id,
        "gauge",
        "CPU Usage",
        {"x": 6, "y": 0, "width": 3, "height": 4},
        ["system.cpu"]
    )
    
    # Update metrics
    await system.update_metric("api.latency", 45.2)
    await system.update_metric("system.cpu", 67.8)
    
    # Get analytics
    analytics = await system.get_dashboard_analytics(dashboard_id)
    print(f"Dashboard analytics: {analytics}")
    
    await system.shutdown()

if __name__ == "__main__":
    asyncio.run(demo_dashboard())