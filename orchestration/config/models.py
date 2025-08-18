"""Configuration data models for the orchestration system."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from pathlib import Path


class ServiceType(Enum):
    """Types of services that can be managed."""
    BACKEND = "backend"
    FRONTEND = "frontend"
    MOBILE = "mobile"
    DESKTOP = "desktop"
    INFRASTRUCTURE = "infrastructure"


class EnvironmentType(Enum):
    """Environment types for configuration."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class ServiceConfig:
    """Configuration for a single service."""
    name: str
    type: ServiceType
    port: int
    health_check_url: str
    startup_command: str
    environment_variables: Dict[str, str] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    working_directory: Optional[str] = None
    timeout: int = 30
    restart_policy: str = "on-failure"
    max_restarts: int = 3


@dataclass
class BackendConfig:
    """Backend service configuration."""
    api_port: int = 8000
    streamlit_port: int = 8501
    debug: bool = True
    workers: int = 1
    reload: bool = True


@dataclass
class FrontendConfig:
    """Frontend application configuration."""
    port: int = 3000
    api_url: str = "http://localhost:8000"
    build_command: str = "npm run build"
    dev_command: str = "npm run dev"


@dataclass
class MobileConfig:
    """Mobile application configuration."""
    api_url: str = "http://localhost:8000"
    dev_mode: bool = True
    platform: str = "ios"  # ios, android, both
    metro_port: int = 8081


@dataclass
class DesktopConfig:
    """Desktop application configuration."""
    api_url: str = "http://localhost:8000"
    auto_updater: bool = False
    dev_mode: bool = True


@dataclass
class InfrastructureConfig:
    """Infrastructure services configuration."""
    postgres: Dict[str, Any] = field(default_factory=lambda: {
        "host": "localhost",
        "port": 5432,
        "database": "transcription_dev",
        "username": "postgres",
        "password": "postgres"
    })
    redis: Dict[str, Any] = field(default_factory=lambda: {
        "host": "localhost",
        "port": 6379,
        "db": 0
    })
    minio: Dict[str, Any] = field(default_factory=lambda: {
        "endpoint": "localhost:9000",
        "access_key": "minioadmin",
        "secret_key": "minioadmin",
        "secure": False
    })


@dataclass
class EnvironmentConfig:
    """Configuration for a specific environment."""
    name: str
    backend: BackendConfig = field(default_factory=BackendConfig)
    frontend: FrontendConfig = field(default_factory=FrontendConfig)
    mobile: MobileConfig = field(default_factory=MobileConfig)
    desktop: DesktopConfig = field(default_factory=DesktopConfig)
    infrastructure: InfrastructureConfig = field(default_factory=InfrastructureConfig)


@dataclass
class SystemConfig:
    """Complete system configuration."""
    environment: str
    services: Dict[str, ServiceConfig] = field(default_factory=dict)
    environments: Dict[str, EnvironmentConfig] = field(default_factory=dict)
    logging: Dict[str, Any] = field(default_factory=dict)
    monitoring: Dict[str, Any] = field(default_factory=dict)
    testing: Dict[str, Any] = field(default_factory=dict)
    deployment: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfigChange:
    """Represents a configuration change event."""
    file_path: str
    change_type: str  # created, modified, deleted
    timestamp: float
    old_config: Optional[Dict[str, Any]] = None
    new_config: Optional[Dict[str, Any]] = None


@dataclass
class ValidationResult:
    """Result of configuration validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)