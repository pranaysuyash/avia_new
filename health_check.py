#!/usr/bin/env python3
"""
Health Check and Monitoring Module
Provides health check endpoints and system monitoring capabilities
"""

import os
import time
import psutil
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import requests
from config import Config

logger = logging.getLogger(__name__)

class HealthChecker:
    """System health monitoring and status checking"""
    
    def __init__(self):
        self.start_time = time.time()
        self.last_check = None
        self.check_history = []
        self.max_history = 100
        
    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status"""
        try:
            # Basic system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Application uptime
            uptime_seconds = time.time() - self.start_time
            uptime_str = str(timedelta(seconds=int(uptime_seconds)))
            
            # Check API connectivity
            api_status = self._check_api_connectivity()
            
            # Check disk space for temp directory
            temp_dir_status = self._check_temp_directory()
            
            # Overall health status
            is_healthy = (
                cpu_percent < 90 and
                memory.percent < 90 and
                disk.percent < 90 and
                api_status.get('openai', {}).get('status') != 'error' and
                temp_dir_status['status'] == 'ok'
            )
            
            health_data = {
                'status': 'healthy' if is_healthy else 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'uptime': uptime_str,
                'uptime_seconds': int(uptime_seconds),
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory': {
                        'total': memory.total,
                        'available': memory.available,
                        'percent': memory.percent,
                        'used': memory.used
                    },
                    'disk': {
                        'total': disk.total,
                        'free': disk.free,
                        'percent': disk.percent,
                        'used': disk.used
                    }
                },
                'apis': api_status,
                'temp_directory': temp_dir_status,
                'configuration': self._check_configuration(),
                'version': self._get_version_info()
            }
            
            # Store in history
            self._update_history(health_data)
            self.last_check = datetime.utcnow()
            
            return health_data
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'error',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }
    
    def get_simple_health(self) -> Dict[str, str]:
        """Get simple health status for basic health checks"""
        try:
            # Quick checks only
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            
            # Check if critical services are responsive
            is_healthy = cpu_percent < 95 and memory_percent < 95
            
            return {
                'status': 'ok' if is_healthy else 'error',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'error',
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            }
    
    def _check_api_connectivity(self) -> Dict[str, Dict[str, Any]]:
        """Check connectivity to external APIs"""
        api_status = {}
        
        # Check OpenAI API
        if Config.OPENAI_API_KEY:
            try:
                headers = {'Authorization': f'Bearer {Config.OPENAI_API_KEY}'}
                response = requests.get(
                    'https://api.openai.com/v1/models',
                    headers=headers,
                    timeout=10
                )
                api_status['openai'] = {
                    'status': 'ok' if response.status_code == 200 else 'error',
                    'response_time': response.elapsed.total_seconds(),
                    'status_code': response.status_code
                }
            except Exception as e:
                api_status['openai'] = {
                    'status': 'error',
                    'error': str(e)
                }
        else:
            api_status['openai'] = {
                'status': 'not_configured',
                'message': 'API key not configured'
            }
        
        # Check ElevenLabs API
        if Config.ELEVENLABS_API_KEY:
            try:
                headers = {'xi-api-key': Config.ELEVENLABS_API_KEY}
                response = requests.get(
                    'https://api.elevenlabs.io/v1/voices',
                    headers=headers,
                    timeout=10
                )
                api_status['elevenlabs'] = {
                    'status': 'ok' if response.status_code == 200 else 'error',
                    'response_time': response.elapsed.total_seconds(),
                    'status_code': response.status_code
                }
            except Exception as e:
                api_status['elevenlabs'] = {
                    'status': 'error',
                    'error': str(e)
                }
        else:
            api_status['elevenlabs'] = {
                'status': 'not_configured',
                'message': 'API key not configured'
            }
        
        return api_status
    
    def _check_temp_directory(self) -> Dict[str, Any]:
        """Check temp directory status and available space"""
        try:
            temp_dir = Config.TEMP_DIR
            
            # Check if directory exists and is writable
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir, exist_ok=True)
            
            # Check write permissions
            test_file = os.path.join(temp_dir, '.health_check')
            try:
                with open(test_file, 'w') as f:
                    f.write('health_check')
                os.remove(test_file)
                writable = True
            except Exception:
                writable = False
            
            # Check available space
            disk_usage = psutil.disk_usage(temp_dir)
            free_space_mb = disk_usage.free / (1024 * 1024)
            
            return {
                'status': 'ok' if writable and free_space_mb > 100 else 'warning',
                'path': temp_dir,
                'writable': writable,
                'free_space_mb': int(free_space_mb),
                'total_space_mb': int(disk_usage.total / (1024 * 1024))
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _check_configuration(self) -> Dict[str, Any]:
        """Check application configuration status"""
        try:
            is_valid, issues = Config.validate_configuration()
            api_keys = Config.validate_api_keys()
            
            return {
                'status': 'ok' if is_valid else 'warning',
                'valid': is_valid,
                'issues': issues,
                'api_keys_configured': api_keys
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _get_version_info(self) -> Dict[str, str]:
        """Get application version information"""
        try:
            # Try to read version from file or environment
            version = os.getenv('APP_VERSION', 'unknown')
            build_date = os.getenv('BUILD_DATE', 'unknown')
            git_commit = os.getenv('GIT_COMMIT', 'unknown')
            
            return {
                'version': version,
                'build_date': build_date,
                'git_commit': git_commit[:8] if git_commit != 'unknown' else git_commit
            }
        except Exception:
            return {
                'version': 'unknown',
                'build_date': 'unknown',
                'git_commit': 'unknown'
            }
    
    def _update_history(self, health_data: Dict[str, Any]):
        """Update health check history"""
        # Keep only essential data for history
        history_entry = {
            'timestamp': health_data['timestamp'],
            'status': health_data['status'],
            'cpu_percent': health_data['system']['cpu_percent'],
            'memory_percent': health_data['system']['memory']['percent'],
            'disk_percent': health_data['system']['disk']['percent']
        }
        
        self.check_history.append(history_entry)
        
        # Keep only recent history
        if len(self.check_history) > self.max_history:
            self.check_history = self.check_history[-self.max_history:]
    
    def get_health_history(self) -> Dict[str, Any]:
        """Get health check history"""
        return {
            'history': self.check_history,
            'total_checks': len(self.check_history),
            'last_check': self.last_check.isoformat() if self.last_check else None
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics for monitoring systems (Prometheus format)"""
        try:
            health = self.get_system_health()
            
            metrics = {
                'app_uptime_seconds': health['uptime_seconds'],
                'system_cpu_percent': health['system']['cpu_percent'],
                'system_memory_percent': health['system']['memory']['percent'],
                'system_disk_percent': health['system']['disk']['percent'],
                'system_memory_available_bytes': health['system']['memory']['available'],
                'system_disk_free_bytes': health['system']['disk']['free'],
                'api_openai_status': 1 if health['apis'].get('openai', {}).get('status') == 'ok' else 0,
                'api_elevenlabs_status': 1 if health['apis'].get('elevenlabs', {}).get('status') == 'ok' else 0,
                'temp_directory_status': 1 if health['temp_directory']['status'] == 'ok' else 0,
                'configuration_valid': 1 if health['configuration']['valid'] else 0
            }
            
            # Add API response times if available
            if 'response_time' in health['apis'].get('openai', {}):
                metrics['api_openai_response_time_seconds'] = health['apis']['openai']['response_time']
            
            if 'response_time' in health['apis'].get('elevenlabs', {}):
                metrics['api_elevenlabs_response_time_seconds'] = health['apis']['elevenlabs']['response_time']
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return {}

# Global health checker instance
_health_checker = None

def get_health_checker() -> HealthChecker:
    """Get global health checker instance"""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker

def health_check_endpoint() -> Dict[str, Any]:
    """Health check endpoint for load balancers"""
    return get_health_checker().get_simple_health()

def detailed_health_endpoint() -> Dict[str, Any]:
    """Detailed health check endpoint for monitoring"""
    return get_health_checker().get_system_health()

def metrics_endpoint() -> Dict[str, Any]:
    """Metrics endpoint for Prometheus"""
    return get_health_checker().get_metrics()

if __name__ == "__main__":
    # Test health checker
    checker = HealthChecker()
    health = checker.get_system_health()
    print("Health Check Results:")
    print(f"Status: {health['status']}")
    print(f"Uptime: {health['uptime']}")
    print(f"CPU: {health['system']['cpu_percent']}%")
    print(f"Memory: {health['system']['memory']['percent']}%")
    print(f"Disk: {health['system']['disk']['percent']}%")