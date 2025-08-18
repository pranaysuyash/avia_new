"""Core types and enums for the orchestration system."""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass


class ServiceType(Enum):
    """Types of services that can be managed."""
    BACKEND = "backend"
    FRONTEND = "frontend"
    MOBILE = "mobile"
    DESKTOP = "desktop"
    INFRASTRUCTURE = "infrastructure"


class ServiceStatus(Enum):
    """Service status enumeration."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAILED = "failed"
    UNKNOWN = "unknown"


class SystemHealth(Enum):
    """Overall system health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ServiceInfo:
    """Information about a running service."""
    name: str
    service_type: ServiceType
    status: ServiceStatus
    pid: Optional[int] = None
    port: Optional[int] = None
    start_time: Optional[float] = None
    restart_count: int = 0
    last_health_check: Optional[float] = None
    health_status: str = "unknown"
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'service_type': self.service_type.value,
            'status': self.status.value,
            'pid': self.pid,
            'port': self.port,
            'start_time': self.start_time,
            'restart_count': self.restart_count,
            'last_health_check': self.last_health_check,
            'health_status': self.health_status,
            'error_message': self.error_message
        }


@dataclass
class StartupResult:
    """Result of service startup operation."""
    success: bool
    service_info: Optional[ServiceInfo] = None
    error_message: Optional[str] = None
    pid: Optional[int] = None