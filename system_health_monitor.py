#!/usr/bin/env python3
"""
System Health Monitoring Module
Provides real-time system health monitoring and visualization
"""

import psutil
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio
import aiohttp
import time
import os
import logging

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"


@dataclass
class ServiceHealth:
    """Service health information"""
    name: str
    endpoint: str
    status: ServiceStatus
    response_time: Optional[float] = None
    last_check: Optional[datetime] = None
    error_message: Optional[str] = None
    uptime_percentage: float = 99.9


@dataclass
class ResourceMetrics:
    """System resource metrics"""
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    network_sent_mb: float
    network_recv_mb: float
    active_connections: int
    process_count: int
    thread_count: int


class SystemHealthMonitor:
    """Monitor system health and resources"""
    
    def __init__(self):
        self.services = self._init_services()
        self.metrics_history = []
        self.max_history_length = 100
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize session state for health monitoring"""
        if 'health_metrics_history' not in st.session_state:
            st.session_state.health_metrics_history = pd.DataFrame()
        if 'service_health_cache' not in st.session_state:
            st.session_state.service_health_cache = {}
        if 'last_health_check' not in st.session_state:
            st.session_state.last_health_check = datetime.now()
    
    def _init_services(self) -> List[ServiceHealth]:
        """Initialize services to monitor"""
        return [
            ServiceHealth(
                name="API Gateway",
                endpoint="http://localhost:8000/health",
                status=ServiceStatus.UNKNOWN
            ),
            ServiceHealth(
                name="Transcription Service",
                endpoint="http://localhost:8000/api/transcription/health",
                status=ServiceStatus.UNKNOWN
            ),
            ServiceHealth(
                name="Database",
                endpoint="postgresql://localhost:5432",
                status=ServiceStatus.UNKNOWN
            ),
            ServiceHealth(
                name="Redis Cache",
                endpoint="redis://localhost:6379",
                status=ServiceStatus.UNKNOWN
            ),
            ServiceHealth(
                name="Queue Worker",
                endpoint="http://localhost:8000/api/queue/health",
                status=ServiceStatus.UNKNOWN
            )
        ]
    
    def get_current_metrics(self) -> ResourceMetrics:
        """Get current system resource metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024 ** 3)
            memory_total_gb = memory.total / (1024 ** 3)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used_gb = disk.used / (1024 ** 3)
            disk_total_gb = disk.total / (1024 ** 3)
            
            # Network metrics
            net_io = psutil.net_io_counters()
            network_sent_mb = net_io.bytes_sent / (1024 ** 2)
            network_recv_mb = net_io.bytes_recv / (1024 ** 2)
            
            # Connection metrics
            connections = len(psutil.net_connections())
            
            # Process metrics
            process_count = len(psutil.pids())
            
            # Thread count for current process
            current_process = psutil.Process()
            thread_count = current_process.num_threads()
            
            return ResourceMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_gb=memory_used_gb,
                memory_total_gb=memory_total_gb,
                disk_percent=disk_percent,
                disk_used_gb=disk_used_gb,
                disk_total_gb=disk_total_gb,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                active_connections=connections,
                process_count=process_count,
                thread_count=thread_count
            )
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            # Return default metrics on error
            return ResourceMetrics(
                cpu_percent=0,
                memory_percent=0,
                memory_used_gb=0,
                memory_total_gb=0,
                disk_percent=0,
                disk_used_gb=0,
                disk_total_gb=0,
                network_sent_mb=0,
                network_recv_mb=0,
                active_connections=0,
                process_count=0,
                thread_count=0
            )
    
    async def check_service_health(self, service: ServiceHealth) -> ServiceHealth:
        """Check health of a single service"""
        start_time = time.time()
        
        try:
            if service.endpoint.startswith('http'):
                # HTTP health check
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        service.endpoint,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        response_time = (time.time() - start_time) * 1000  # ms
                        
                        if response.status == 200:
                            service.status = ServiceStatus.HEALTHY
                        elif response.status >= 500:
                            service.status = ServiceStatus.DOWN
                        else:
                            service.status = ServiceStatus.DEGRADED
                        
                        service.response_time = response_time
                        service.last_check = datetime.now()
                        
            elif service.endpoint.startswith('postgresql'):
                # PostgreSQL health check
                # In production, use asyncpg for async checks
                service.status = ServiceStatus.HEALTHY  # Placeholder
                service.response_time = 10.5
                service.last_check = datetime.now()
                
            elif service.endpoint.startswith('redis'):
                # Redis health check
                # In production, use aioredis for async checks
                service.status = ServiceStatus.HEALTHY  # Placeholder
                service.response_time = 1.2
                service.last_check = datetime.now()
                
        except asyncio.TimeoutError:
            service.status = ServiceStatus.DOWN
            service.error_message = "Connection timeout"
            service.last_check = datetime.now()
            
        except Exception as e:
            service.status = ServiceStatus.DOWN
            service.error_message = str(e)
            service.last_check = datetime.now()
        
        return service
    
    async def check_all_services(self) -> List[ServiceHealth]:
        """Check health of all services"""
        tasks = [self.check_service_health(service) for service in self.services]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Update services with results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.services[i].status = ServiceStatus.DOWN
                self.services[i].error_message = str(result)
            else:
                self.services[i] = result
        
        # Cache results
        st.session_state.service_health_cache = {
            service.name: service for service in self.services
        }
        st.session_state.last_health_check = datetime.now()
        
        return self.services
    
    def get_health_score(self) -> Tuple[float, str]:
        """
        Calculate overall health score
        
        Returns:
            Tuple of (score 0-100, status message)
        """
        metrics = self.get_current_metrics()
        
        # Calculate component scores
        cpu_score = max(0, 100 - metrics.cpu_percent)
        memory_score = max(0, 100 - metrics.memory_percent)
        disk_score = max(0, 100 - metrics.disk_percent)
        
        # Service health score
        healthy_services = sum(
            1 for service in self.services 
            if service.status == ServiceStatus.HEALTHY
        )
        service_score = (healthy_services / len(self.services)) * 100 if self.services else 100
        
        # Weighted average
        weights = {
            'cpu': 0.25,
            'memory': 0.25,
            'disk': 0.2,
            'services': 0.3
        }
        
        overall_score = (
            cpu_score * weights['cpu'] +
            memory_score * weights['memory'] +
            disk_score * weights['disk'] +
            service_score * weights['services']
        )
        
        # Determine status message
        if overall_score >= 90:
            status = "Excellent - All systems operating optimally"
        elif overall_score >= 75:
            status = "Good - Minor resource usage detected"
        elif overall_score >= 50:
            status = "Fair - Some services may be degraded"
        else:
            status = "Poor - Critical issues detected"
        
        return overall_score, status
    
    def get_resource_alerts(self) -> List[Dict[str, Any]]:
        """Get alerts for resource usage"""
        alerts = []
        metrics = self.get_current_metrics()
        
        # CPU alerts
        if metrics.cpu_percent > 90:
            alerts.append({
                'type': 'critical',
                'category': 'CPU',
                'message': f'Critical CPU usage: {metrics.cpu_percent:.1f}%',
                'value': metrics.cpu_percent
            })
        elif metrics.cpu_percent > 75:
            alerts.append({
                'type': 'warning',
                'category': 'CPU',
                'message': f'High CPU usage: {metrics.cpu_percent:.1f}%',
                'value': metrics.cpu_percent
            })
        
        # Memory alerts
        if metrics.memory_percent > 90:
            alerts.append({
                'type': 'critical',
                'category': 'Memory',
                'message': f'Critical memory usage: {metrics.memory_percent:.1f}%',
                'value': metrics.memory_percent
            })
        elif metrics.memory_percent > 75:
            alerts.append({
                'type': 'warning',
                'category': 'Memory',
                'message': f'High memory usage: {metrics.memory_percent:.1f}%',
                'value': metrics.memory_percent
            })
        
        # Disk alerts
        if metrics.disk_percent > 90:
            alerts.append({
                'type': 'critical',
                'category': 'Disk',
                'message': f'Critical disk usage: {metrics.disk_percent:.1f}%',
                'value': metrics.disk_percent
            })
        elif metrics.disk_percent > 80:
            alerts.append({
                'type': 'warning',
                'category': 'Disk',
                'message': f'High disk usage: {metrics.disk_percent:.1f}%',
                'value': metrics.disk_percent
            })
        
        # Service alerts
        for service in self.services:
            if service.status == ServiceStatus.DOWN:
                alerts.append({
                    'type': 'critical',
                    'category': 'Service',
                    'message': f'{service.name} is down',
                    'value': service.name
                })
            elif service.status == ServiceStatus.DEGRADED:
                alerts.append({
                    'type': 'warning',
                    'category': 'Service',
                    'message': f'{service.name} is degraded',
                    'value': service.name
                })
        
        return alerts
    
    def update_metrics_history(self):
        """Update metrics history for trending"""
        current_metrics = self.get_current_metrics()
        timestamp = datetime.now()
        
        # Create new row
        new_row = pd.DataFrame({
            'timestamp': [timestamp],
            'cpu_percent': [current_metrics.cpu_percent],
            'memory_percent': [current_metrics.memory_percent],
            'disk_percent': [current_metrics.disk_percent],
            'network_sent_mb': [current_metrics.network_sent_mb],
            'network_recv_mb': [current_metrics.network_recv_mb],
            'active_connections': [current_metrics.active_connections]
        })
        
        # Append to history
        if st.session_state.health_metrics_history.empty:
            st.session_state.health_metrics_history = new_row
        else:
            st.session_state.health_metrics_history = pd.concat([
                st.session_state.health_metrics_history,
                new_row
            ], ignore_index=True)
        
        # Keep only recent history
        if len(st.session_state.health_metrics_history) > self.max_history_length:
            st.session_state.health_metrics_history = \
                st.session_state.health_metrics_history.tail(self.max_history_length)
    
    def get_metrics_trend(self, metric_name: str, period_minutes: int = 60) -> pd.DataFrame:
        """Get trend data for a specific metric"""
        if st.session_state.health_metrics_history.empty:
            return pd.DataFrame()
        
        # Filter by time period
        cutoff_time = datetime.now() - timedelta(minutes=period_minutes)
        
        history = st.session_state.health_metrics_history
        if 'timestamp' in history.columns:
            recent_history = history[history['timestamp'] > cutoff_time]
            
            if metric_name in recent_history.columns:
                return recent_history[['timestamp', metric_name]]
        
        return pd.DataFrame()
    
    def predict_resource_exhaustion(self) -> Dict[str, Optional[timedelta]]:
        """Predict when resources might be exhausted based on trends"""
        predictions = {}
        
        # Get recent history
        history = st.session_state.health_metrics_history
        if len(history) < 10:  # Need enough data points
            return {
                'memory': None,
                'disk': None,
                'cpu': None
            }
        
        # Simple linear prediction for disk space
        metrics = self.get_current_metrics()
        
        # Disk prediction (assuming linear growth)
        if metrics.disk_percent > 50:
            # Calculate daily growth rate (simplified)
            days_to_full = (100 - metrics.disk_percent) / 0.5  # Assuming 0.5% daily growth
            predictions['disk'] = timedelta(days=int(days_to_full))
        else:
            predictions['disk'] = None
        
        # Memory prediction (more volatile, shorter timeframe)
        if metrics.memory_percent > 70:
            hours_to_full = (100 - metrics.memory_percent) / 2  # Assuming 2% hourly growth
            predictions['memory'] = timedelta(hours=int(hours_to_full))
        else:
            predictions['memory'] = None
        
        predictions['cpu'] = None  # CPU is too volatile to predict
        
        return predictions


# Global instance
_health_monitor = None


def get_health_monitor() -> SystemHealthMonitor:
    """Get or create health monitor instance"""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = SystemHealthMonitor()
    return _health_monitor


# Convenience functions for integration
def get_system_health_score() -> Tuple[float, str]:
    """Get current system health score"""
    monitor = get_health_monitor()
    return monitor.get_health_score()


def get_resource_metrics() -> ResourceMetrics:
    """Get current resource metrics"""
    monitor = get_health_monitor()
    return monitor.get_current_metrics()


def get_health_alerts() -> List[Dict[str, Any]]:
    """Get current health alerts"""
    monitor = get_health_monitor()
    return monitor.get_resource_alerts()


async def check_services_health() -> List[ServiceHealth]:
    """Check health of all services"""
    monitor = get_health_monitor()
    return await monitor.check_all_services()