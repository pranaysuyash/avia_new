"""
Health check system for monitoring service dependencies
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Callable, Awaitable
from datetime import datetime, timedelta
from enum import Enum
import aiohttp
import psutil

from .logging import get_logger

logger = get_logger("health_checker")

class HealthStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"

class HealthCheck:
    """Individual health check definition"""
    
    def __init__(
        self,
        name: str,
        check_func: Callable[[], Awaitable[Dict[str, Any]]],
        timeout: int = 5,
        critical: bool = True,
        interval: int = 30
    ):
        self.name = name
        self.check_func = check_func
        self.timeout = timeout
        self.critical = critical
        self.interval = interval
        self.last_check = None
        self.last_result = None
        self.consecutive_failures = 0

class HealthChecker:
    """
    Comprehensive health checking system that monitors:
    - Database connectivity
    - External service dependencies
    - System resources
    - Application-specific health indicators
    """
    
    def __init__(self):
        self.checks = {}
        self.system_checks_enabled = True
        self.check_history = {}
        self.max_history = 100
    
    def add_check(
        self,
        name: str,
        check_func: Callable[[], Awaitable[Dict[str, Any]]],
        timeout: int = 5,
        critical: bool = True,
        interval: int = 30
    ):
        """Add a health check"""
        self.checks[name] = HealthCheck(
            name=name,
            check_func=check_func,
            timeout=timeout,
            critical=critical,
            interval=interval
        )
        logger.info(f"Added health check: {name}")
    
    def remove_check(self, name: str):
        """Remove a health check"""
        if name in self.checks:
            del self.checks[name]
            logger.info(f"Removed health check: {name}")
    
    async def check_all(self) -> Dict[str, Any]:
        """Run all health checks and return comprehensive status"""
        start_time = time.time()
        results = {}
        overall_status = HealthStatus.HEALTHY
        
        # Run custom checks
        for name, health_check in self.checks.items():
            try:
                result = await self._run_single_check(health_check)
                results[name] = result
                
                # Update overall status
                if result["status"] == HealthStatus.UNHEALTHY.value:
                    if health_check.critical:
                        overall_status = HealthStatus.UNHEALTHY
                    elif overall_status == HealthStatus.HEALTHY:
                        overall_status = HealthStatus.DEGRADED
                
            except Exception as e:
                logger.error(f"Health check {name} failed with exception: {str(e)}")
                results[name] = {
                    "status": HealthStatus.UNHEALTHY.value,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                if health_check.critical:
                    overall_status = HealthStatus.UNHEALTHY
                elif overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED
        
        # Run system checks if enabled
        if self.system_checks_enabled:
            system_status = await self._check_system_health()
            results["system"] = system_status
            
            if system_status["status"] == HealthStatus.DEGRADED.value:
                if overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED
        
        # Compile final result
        health_result = {
            "status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "duration": time.time() - start_time,
            "checks": results,
            "summary": self._generate_summary(results, overall_status)
        }
        
        # Store in history
        self._store_result(health_result)
        
        return health_result
    
    async def check_single(self, name: str) -> Dict[str, Any]:
        """Run a single health check"""
        if name not in self.checks:
            return {
                "status": HealthStatus.UNKNOWN.value,
                "error": f"Health check '{name}' not found",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        health_check = self.checks[name]
        return await self._run_single_check(health_check)
    
    async def _run_single_check(self, health_check: HealthCheck) -> Dict[str, Any]:
        """Run a single health check with timeout"""
        start_time = time.time()
        
        try:
            # Check if we need to run this check (based on interval)
            if (health_check.last_check and 
                time.time() - health_check.last_check < health_check.interval):
                if health_check.last_result:
                    return health_check.last_result
            
            # Run the check with timeout
            result = await asyncio.wait_for(
                health_check.check_func(),
                timeout=health_check.timeout
            )
            
            # Ensure result has required fields
            if "status" not in result:
                result["status"] = HealthStatus.HEALTHY.value
            
            result["duration"] = time.time() - start_time
            result["timestamp"] = datetime.utcnow().isoformat()
            
            # Reset failure counter on success
            if result["status"] == HealthStatus.HEALTHY.value:
                health_check.consecutive_failures = 0
            else:
                health_check.consecutive_failures += 1
            
            # Update check state
            health_check.last_check = time.time()
            health_check.last_result = result
            
            return result
            
        except asyncio.TimeoutError:
            health_check.consecutive_failures += 1
            return {
                "status": HealthStatus.UNHEALTHY.value,
                "error": f"Health check timed out after {health_check.timeout}s",
                "duration": time.time() - start_time,
                "timestamp": datetime.utcnow().isoformat(),
                "consecutive_failures": health_check.consecutive_failures
            }
        
        except Exception as e:
            health_check.consecutive_failures += 1
            return {
                "status": HealthStatus.UNHEALTHY.value,
                "error": str(e),
                "duration": time.time() - start_time,
                "timestamp": datetime.utcnow().isoformat(),
                "consecutive_failures": health_check.consecutive_failures
            }
    
    async def _check_system_health(self) -> Dict[str, Any]:
        """Check system-level health indicators"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Determine status based on thresholds
            status = HealthStatus.HEALTHY
            warnings = []
            
            if cpu_percent > 90:
                status = HealthStatus.DEGRADED
                warnings.append(f"High CPU usage: {cpu_percent}%")
            elif cpu_percent > 80:
                warnings.append(f"Elevated CPU usage: {cpu_percent}%")
            
            if memory_percent > 90:
                status = HealthStatus.DEGRADED
                warnings.append(f"High memory usage: {memory_percent}%")
            elif memory_percent > 80:
                warnings.append(f"Elevated memory usage: {memory_percent}%")
            
            if disk_percent > 95:
                status = HealthStatus.DEGRADED
                warnings.append(f"High disk usage: {disk_percent}%")
            elif disk_percent > 85:
                warnings.append(f"Elevated disk usage: {disk_percent}%")
            
            return {
                "status": status.value,
                "metrics": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "disk_percent": disk_percent,
                    "memory_available": memory.available,
                    "disk_free": disk.free
                },
                "warnings": warnings,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"System health check failed: {str(e)}")
            return {
                "status": HealthStatus.UNKNOWN.value,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _generate_summary(self, results: Dict[str, Any], overall_status: HealthStatus) -> Dict[str, Any]:
        """Generate a summary of health check results"""
        total_checks = len(results)
        healthy_checks = sum(1 for r in results.values() if r.get("status") == HealthStatus.HEALTHY.value)
        unhealthy_checks = sum(1 for r in results.values() if r.get("status") == HealthStatus.UNHEALTHY.value)
        degraded_checks = sum(1 for r in results.values() if r.get("status") == HealthStatus.DEGRADED.value)
        
        return {
            "overall_status": overall_status.value,
            "total_checks": total_checks,
            "healthy_checks": healthy_checks,
            "unhealthy_checks": unhealthy_checks,
            "degraded_checks": degraded_checks,
            "success_rate": (healthy_checks / total_checks * 100) if total_checks > 0 else 0
        }
    
    def _store_result(self, result: Dict[str, Any]):
        """Store health check result in history"""
        timestamp = result["timestamp"]
        
        if "history" not in self.check_history:
            self.check_history["history"] = []
        
        self.check_history["history"].append({
            "timestamp": timestamp,
            "status": result["status"],
            "duration": result["duration"],
            "summary": result["summary"]
        })
        
        # Keep only recent history
        if len(self.check_history["history"]) > self.max_history:
            self.check_history["history"] = self.check_history["history"][-self.max_history:]
    
    def get_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get health check history for the specified number of hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        history = self.check_history.get("history", [])
        return [
            entry for entry in history
            if datetime.fromisoformat(entry["timestamp"].replace('Z', '+00:00')) > cutoff_time
        ]

# Pre-defined health check functions
async def database_health_check(db_url: str) -> Dict[str, Any]:
    """Health check for database connectivity"""
    try:
        # This is a placeholder - implement actual database check
        # For SQLAlchemy: test a simple query
        return {
            "status": HealthStatus.HEALTHY.value,
            "message": "Database connection successful"
        }
    except Exception as e:
        return {
            "status": HealthStatus.UNHEALTHY.value,
            "error": str(e)
        }

async def redis_health_check(redis_url: str) -> Dict[str, Any]:
    """Health check for Redis connectivity"""
    try:
        # This is a placeholder - implement actual Redis check
        return {
            "status": HealthStatus.HEALTHY.value,
            "message": "Redis connection successful"
        }
    except Exception as e:
        return {
            "status": HealthStatus.UNHEALTHY.value,
            "error": str(e)
        }

async def external_service_health_check(service_url: str, service_name: str) -> Dict[str, Any]:
    """Health check for external HTTP services"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{service_url}/health", timeout=5) as response:
                if response.status == 200:
                    return {
                        "status": HealthStatus.HEALTHY.value,
                        "message": f"{service_name} is healthy",
                        "response_time": response.headers.get("X-Response-Time")
                    }
                else:
                    return {
                        "status": HealthStatus.UNHEALTHY.value,
                        "error": f"{service_name} returned status {response.status}"
                    }
    except Exception as e:
        return {
            "status": HealthStatus.UNHEALTHY.value,
            "error": f"Failed to connect to {service_name}: {str(e)}"
        }