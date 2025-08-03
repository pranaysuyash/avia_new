#!/usr/bin/env python3
"""
System Monitoring Service
Monitors system health, performance, and resources
"""

import logging
import psutil
import os
import redis
import boto3
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
from sqlalchemy import func
from sqlalchemy.orm import Session

from database.models import User, Transcript
from database.connection import get_db, engine

logger = logging.getLogger(__name__)

class SystemMonitoringService:
    """Service for monitoring system health and performance"""
    
    def __init__(self):
        self.redis_client = self._init_redis()
        self.s3_client = self._init_s3()
    
    def _init_redis(self) -> Optional[redis.Redis]:
        """Initialize Redis client"""
        try:
            client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=0,
                decode_responses=True
            )
            client.ping()
            return client
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            return None
    
    def _init_s3(self) -> Optional[boto3.client]:
        """Initialize S3 client"""
        try:
            if os.getenv('AWS_ACCESS_KEY_ID'):
                return boto3.client(
                    's3',
                    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                    region_name=os.getenv('AWS_REGION', 'us-east-1')
                )
        except Exception as e:
            logger.warning(f"S3 client initialization failed: {e}")
        return None
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            
            # Network metrics
            network = psutil.net_io_counters()
            
            # Process metrics
            process = psutil.Process()
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count,
                    'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'used': memory.used,
                    'percent': memory.percent
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': disk.percent
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                },
                'process': {
                    'memory_mb': process.memory_info().rss / 1024 / 1024,
                    'cpu_percent': process.cpu_percent(),
                    'num_threads': process.num_threads(),
                    'open_files': len(process.open_files())
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}
    
    def check_service_health(self) -> Dict[str, Dict[str, Any]]:
        """Check health of all services"""
        services = {}
        
        # Check API
        services['api'] = {
            'status': 'operational',
            'uptime': self._get_process_uptime(),
            'response_time': 0
        }
        
        # Check Database
        services['database'] = self._check_database_health()
        
        # Check Redis
        services['redis'] = self._check_redis_health()
        
        # Check Storage
        services['storage'] = self._check_storage_health()
        
        # Check Email Service
        services['email'] = self._check_email_health()
        
        # Check WebSocket
        services['websocket'] = self._check_websocket_health()
        
        return services
    
    def _check_database_health(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            start_time = datetime.utcnow()
            
            # Test connection
            with engine.connect() as conn:
                result = conn.execute("SELECT 1")
                result.fetchone()
            
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Get connection pool stats
            pool_status = {
                'size': engine.pool.size(),
                'checked_in': engine.pool.checkedin(),
                'overflow': engine.pool.overflow(),
                'total': engine.pool.total_overflow()
            }
            
            return {
                'status': 'operational',
                'response_time': response_time,
                'pool_status': pool_status
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'down',
                'error': str(e)
            }
    
    def _check_redis_health(self) -> Dict[str, Any]:
        """Check Redis health"""
        if not self.redis_client:
            return {'status': 'unavailable'}
        
        try:
            start_time = datetime.utcnow()
            self.redis_client.ping()
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Get Redis info
            info = self.redis_client.info()
            
            return {
                'status': 'operational',
                'response_time': response_time,
                'version': info.get('redis_version', 'unknown'),
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory_human', 'unknown'),
                'uptime_days': info.get('uptime_in_days', 0)
            }
            
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                'status': 'down',
                'error': str(e)
            }
    
    def _check_storage_health(self) -> Dict[str, Any]:
        """Check storage service health"""
        if not self.s3_client:
            # Check local storage
            try:
                storage_path = os.getenv('STORAGE_PATH', '/tmp/storage')
                disk_usage = psutil.disk_usage(storage_path)
                
                return {
                    'status': 'operational',
                    'type': 'local',
                    'total_gb': disk_usage.total / (1024**3),
                    'used_gb': disk_usage.used / (1024**3),
                    'free_gb': disk_usage.free / (1024**3),
                    'percent_used': disk_usage.percent
                }
            except Exception as e:
                return {'status': 'error', 'error': str(e)}
        
        try:
            # Check S3
            bucket_name = os.getenv('S3_BUCKET_NAME')
            self.s3_client.head_bucket(Bucket=bucket_name)
            
            return {
                'status': 'operational',
                'type': 's3',
                'bucket': bucket_name
            }
            
        except Exception as e:
            logger.error(f"Storage health check failed: {e}")
            return {
                'status': 'down',
                'error': str(e)
            }
    
    def _check_email_health(self) -> Dict[str, Any]:
        """Check email service health"""
        # This would check actual email service
        return {
            'status': 'operational',
            'provider': os.getenv('EMAIL_PROVIDER', 'sendgrid')
        }
    
    def _check_websocket_health(self) -> Dict[str, Any]:
        """Check WebSocket server health"""
        # This would check WebSocket server
        return {
            'status': 'operational',
            'connections': 0  # Would get from WebSocket manager
        }
    
    def _get_process_uptime(self) -> float:
        """Get process uptime in seconds"""
        try:
            process = psutil.Process()
            create_time = datetime.fromtimestamp(process.create_time())
            uptime = (datetime.now() - create_time).total_seconds()
            return uptime
        except Exception:
            return 0
    
    def get_performance_metrics(self, minutes: int = 60) -> Dict[str, Any]:
        """Get performance metrics for the last N minutes"""
        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'period_minutes': minutes,
            'api_performance': self._get_api_performance_metrics(minutes),
            'database_performance': self._get_database_performance_metrics(minutes),
            'transcription_performance': self._get_transcription_performance_metrics(minutes)
        }
        
        return metrics
    
    def _get_api_performance_metrics(self, minutes: int) -> Dict[str, Any]:
        """Get API performance metrics"""
        # This would fetch from monitoring service/logs
        return {
            'requests_per_minute': 150,
            'average_response_time_ms': 45,
            'error_rate': 0.02,
            'status_codes': {
                '2xx': 98.5,
                '4xx': 1.3,
                '5xx': 0.2
            }
        }
    
    def _get_database_performance_metrics(self, minutes: int) -> Dict[str, Any]:
        """Get database performance metrics"""
        # This would fetch from database monitoring
        return {
            'queries_per_minute': 450,
            'average_query_time_ms': 12,
            'slow_queries': 3,
            'connection_pool_usage': 0.65
        }
    
    def _get_transcription_performance_metrics(self, minutes: int) -> Dict[str, Any]:
        """Get transcription performance metrics"""
        db = next(get_db())
        try:
            start_time = datetime.utcnow() - timedelta(minutes=minutes)
            
            # Get transcription stats
            stats = db.query(
                func.count(Transcript.id).label('count'),
                func.avg(Transcript.processing_time).label('avg_time'),
                func.max(Transcript.processing_time).label('max_time'),
                func.min(Transcript.processing_time).label('min_time')
            ).filter(
                Transcript.created_at >= start_time
            ).first()
            
            return {
                'transcriptions_completed': stats.count or 0,
                'average_processing_time': float(stats.avg_time or 0),
                'max_processing_time': float(stats.max_time or 0),
                'min_processing_time': float(stats.min_time or 0)
            }
            
        finally:
            db.close()
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get system alerts"""
        alerts = []
        
        # Check system metrics
        metrics = self.get_system_metrics()
        
        # CPU alert
        if metrics.get('cpu', {}).get('percent', 0) > 80:
            alerts.append({
                'id': 'cpu_high',
                'severity': 'warning',
                'title': 'High CPU Usage',
                'description': f"CPU usage at {metrics['cpu']['percent']}%",
                'timestamp': datetime.utcnow()
            })
        
        # Memory alert
        if metrics.get('memory', {}).get('percent', 0) > 85:
            alerts.append({
                'id': 'memory_high',
                'severity': 'warning',
                'title': 'High Memory Usage',
                'description': f"Memory usage at {metrics['memory']['percent']}%",
                'timestamp': datetime.utcnow()
            })
        
        # Disk alert
        if metrics.get('disk', {}).get('percent', 0) > 90:
            alerts.append({
                'id': 'disk_high',
                'severity': 'critical',
                'title': 'Disk Space Low',
                'description': f"Disk usage at {metrics['disk']['percent']}%",
                'timestamp': datetime.utcnow()
            })
        
        # Service health alerts
        services = self.check_service_health()
        for service_name, service_status in services.items():
            if service_status.get('status') != 'operational':
                alerts.append({
                    'id': f'{service_name}_down',
                    'severity': 'critical',
                    'title': f'{service_name.title()} Service Down',
                    'description': f"{service_name} service is not operational",
                    'timestamp': datetime.utcnow()
                })
        
        return alerts
    
    async def monitor_continuously(self, interval: int = 60):
        """Continuously monitor system and store metrics"""
        while True:
            try:
                # Collect metrics
                metrics = self.get_system_metrics()
                health = self.check_service_health()
                alerts = self.get_alerts()
                
                # Store in Redis for real-time access
                if self.redis_client:
                    self.redis_client.setex(
                        'system:metrics:latest',
                        300,  # 5 minute TTL
                        json.dumps(metrics)
                    )
                    
                    self.redis_client.setex(
                        'system:health:latest',
                        300,
                        json.dumps(health)
                    )
                    
                    if alerts:
                        self.redis_client.setex(
                            'system:alerts:latest',
                            300,
                            json.dumps(alerts)
                        )
                
                # Log critical alerts
                for alert in alerts:
                    if alert['severity'] == 'critical':
                        logger.error(f"CRITICAL ALERT: {alert['title']} - {alert['description']}")
                
            except Exception as e:
                logger.error(f"Error in continuous monitoring: {e}")
            
            await asyncio.sleep(interval)

# Global instance
monitoring_service = SystemMonitoringService()

def get_monitoring_service() -> SystemMonitoringService:
    """Get monitoring service instance"""
    return monitoring_service