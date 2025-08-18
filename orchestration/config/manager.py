"""Configuration management system with hot-reload capabilities."""

import json
import yaml
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, AsyncIterator, List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent
import logging
from datetime import datetime

from .models import (
    SystemConfig, ServiceConfig, EnvironmentConfig, ConfigChange, 
    ValidationResult, ServiceType, BackendConfig, FrontendConfig,
    MobileConfig, DesktopConfig, InfrastructureConfig
)
from .validator import ConfigValidator


logger = logging.getLogger(__name__)


class ConfigFileHandler(FileSystemEventHandler):
    """Handles file system events for configuration files."""
    
    def __init__(self, config_manager: 'ConfigurationManager'):
        self.config_manager = config_manager
        
    def on_modified(self, event):
        if not event.is_directory and self._is_config_file(event.src_path):
            asyncio.create_task(self.config_manager._handle_config_change(
                event.src_path, "modified"
            ))
            
    def on_created(self, event):
        if not event.is_directory and self._is_config_file(event.src_path):
            asyncio.create_task(self.config_manager._handle_config_change(
                event.src_path, "created"
            ))
            
    def on_deleted(self, event):
        if not event.is_directory and self._is_config_file(event.src_path):
            asyncio.create_task(self.config_manager._handle_config_change(
                event.src_path, "deleted"
            ))
            
    def _is_config_file(self, file_path: str) -> bool:
        """Check if file is a configuration file."""
        path = Path(file_path)
        return path.suffix.lower() in ['.yaml', '.yml', '.json'] and 'config' in path.name.lower()


class ConfigurationManager:
    """Manages system configuration with hot-reload capabilities."""
    
    def __init__(self, base_config_path: str = "orchestration/configs"):
        self.base_config_path = Path(base_config_path)
        self.validator = ConfigValidator()
        self.current_config: Optional[SystemConfig] = None
        self.config_cache: Dict[str, Any] = {}
        self.change_callbacks: List[callable] = []
        self.observer: Optional[Observer] = None
        self._ensure_config_directory()
        
    def _ensure_config_directory(self):
        """Ensure configuration directory exists."""
        self.base_config_path.mkdir(parents=True, exist_ok=True)
        
        # Create default configuration files if they don't exist
        default_config_path = self.base_config_path / "default.yaml"
        if not default_config_path.exists():
            self._create_default_config(default_config_path)
            
    def _create_default_config(self, config_path: Path):
        """Create default configuration file."""
        default_config = {
            "environment": "development",
            "environments": {
                "development": {
                    "name": "development",
                    "backend": {
                        "api_port": 8000,
                        "streamlit_port": 8501,
                        "debug": True,
                        "workers": 1,
                        "reload": True
                    },
                    "frontend": {
                        "port": 3000,
                        "api_url": "http://localhost:8000",
                        "build_command": "npm run build",
                        "dev_command": "npm run dev"
                    },
                    "mobile": {
                        "api_url": "http://localhost:8000",
                        "dev_mode": True,
                        "platform": "ios",
                        "metro_port": 8081
                    },
                    "desktop": {
                        "api_url": "http://localhost:8000",
                        "auto_updater": False,
                        "dev_mode": True
                    },
                    "infrastructure": {
                        "postgres": {
                            "host": "localhost",
                            "port": 5432,
                            "database": "transcription_dev",
                            "username": "postgres",
                            "password": "postgres"
                        },
                        "redis": {
                            "host": "localhost",
                            "port": 6379,
                            "db": 0
                        },
                        "minio": {
                            "endpoint": "localhost:9000",
                            "access_key": "minioadmin",
                            "secret_key": "minioadmin",
                            "secure": False
                        }
                    }
                }
            },
            "services": {
                "fastapi": {
                    "name": "fastapi",
                    "type": "backend",
                    "port": 8000,
                    "health_check_url": "http://localhost:8000/health",
                    "startup_command": "uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload",
                    "working_directory": ".",
                    "environment_variables": {
                        "PYTHONPATH": ".",
                        "LOG_LEVEL": "INFO"
                    },
                    "dependencies": ["postgres", "redis", "minio"]
                },
                "streamlit": {
                    "name": "streamlit",
                    "type": "backend",
                    "port": 8501,
                    "health_check_url": "http://localhost:8501",
                    "startup_command": "streamlit run app.py --server.port 8501",
                    "working_directory": ".",
                    "environment_variables": {
                        "PYTHONPATH": "."
                    },
                    "dependencies": ["fastapi"]
                },
                "react": {
                    "name": "react",
                    "type": "frontend",
                    "port": 3000,
                    "health_check_url": "http://localhost:3000",
                    "startup_command": "npm run dev",
                    "working_directory": "frontend",
                    "dependencies": ["fastapi"]
                }
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "handlers": ["console", "file"],
                "file_path": "logs/orchestration.log"
            },
            "monitoring": {
                "health_check_interval": 30,
                "metrics_collection_interval": 60,
                "alert_thresholds": {
                    "response_time": 5000,
                    "error_rate": 0.05,
                    "cpu_usage": 0.8,
                    "memory_usage": 0.8
                }
            }
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False, indent=2)
            
    def load_environment_config(self, env: str) -> EnvironmentConfig:
        """Load configuration for specific environment."""
        config_file = self.base_config_path / f"{env}.yaml"
        
        if not config_file.exists():
            config_file = self.base_config_path / "default.yaml"
            
        config_data = self._load_config_file(config_file)
        env_data = config_data.get("environments", {}).get(env, {})
        
        return self._parse_environment_config(env_data)
        
    def load_system_config(self, config_file: Optional[str] = None) -> SystemConfig:
        """Load complete system configuration."""
        if config_file:
            config_path = Path(config_file)
        else:
            config_path = self.base_config_path / "default.yaml"
            
        config_data = self._load_config_file(config_path)
        system_config = self._parse_system_config(config_data)
        
        # Cache the configuration
        self.current_config = system_config
        self.config_cache[str(config_path)] = config_data
        
        return system_config
        
    def validate_configuration(self, config: Optional[SystemConfig] = None) -> ValidationResult:
        """Validate system configuration."""
        if config is None:
            config = self.current_config
            
        if config is None:
            return ValidationResult(
                is_valid=False,
                errors=["No configuration loaded"]
            )
            
        return self.validator.validate_system_config(config)
        
    def propagate_config(self, target_services: List[str]) -> None:
        """Propagate configuration to target services."""
        if not self.current_config:
            logger.error("No configuration loaded for propagation")
            return
            
        for service_name in target_services:
            if service_name in self.current_config.services:
                service_config = self.current_config.services[service_name]
                self._write_service_config(service_config)
            else:
                logger.warning(f"Service '{service_name}' not found in configuration")
                
    def start_config_watching(self) -> None:
        """Start watching configuration files for changes."""
        if self.observer is not None:
            logger.warning("Configuration watching is already started")
            return
            
        self.observer = Observer()
        event_handler = ConfigFileHandler(self)
        self.observer.schedule(
            event_handler,
            str(self.base_config_path),
            recursive=True
        )
        self.observer.start()
        logger.info(f"Started watching configuration directory: {self.base_config_path}")
        
    def stop_config_watching(self) -> None:
        """Stop watching configuration files."""
        if self.observer is not None:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            logger.info("Stopped configuration watching")
            
    def add_change_callback(self, callback: callable) -> None:
        """Add callback for configuration changes."""
        self.change_callbacks.append(callback)
        
    async def watch_config_changes(self) -> AsyncIterator[ConfigChange]:
        """Async generator for configuration changes."""
        # This would be implemented with an async queue in a real implementation
        # For now, this is a placeholder
        while True:
            await asyncio.sleep(1)
            # Yield changes from queue
            yield ConfigChange(
                file_path="example",
                change_type="modified",
                timestamp=datetime.now().timestamp()
            )
            
    async def _handle_config_change(self, file_path: str, change_type: str) -> None:
        """Handle configuration file changes."""
        logger.info(f"Configuration change detected: {change_type} - {file_path}")
        
        try:
            # Reload configuration
            old_config = self.current_config
            new_config = self.load_system_config(file_path)
            
            # Validate new configuration
            validation_result = self.validate_configuration(new_config)
            if not validation_result.is_valid:
                logger.error(f"Invalid configuration: {validation_result.errors}")
                return
                
            # Create change event
            change = ConfigChange(
                file_path=file_path,
                change_type=change_type,
                timestamp=datetime.now().timestamp(),
                old_config=old_config.__dict__ if old_config else None,
                new_config=new_config.__dict__
            )
            
            # Notify callbacks
            for callback in self.change_callbacks:
                try:
                    await callback(change)
                except Exception as e:
                    logger.error(f"Error in config change callback: {e}")
                    
        except Exception as e:
            logger.error(f"Error handling configuration change: {e}")
            
    def _load_config_file(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from file."""
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
        with open(config_path, 'r') as f:
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            elif config_path.suffix.lower() == '.json':
                return json.load(f)
            else:
                raise ValueError(f"Unsupported configuration file format: {config_path.suffix}")
                
    def _parse_system_config(self, config_data: Dict[str, Any]) -> SystemConfig:
        """Parse system configuration from data."""
        services = {}
        for name, service_data in config_data.get("services", {}).items():
            services[name] = ServiceConfig(
                name=service_data["name"],
                type=ServiceType(service_data["type"]),
                port=service_data["port"],
                health_check_url=service_data["health_check_url"],
                startup_command=service_data["startup_command"],
                environment_variables=service_data.get("environment_variables", {}),
                dependencies=service_data.get("dependencies", []),
                working_directory=service_data.get("working_directory"),
                timeout=service_data.get("timeout", 30),
                restart_policy=service_data.get("restart_policy", "on-failure"),
                max_restarts=service_data.get("max_restarts", 3)
            )
            
        environments = {}
        for name, env_data in config_data.get("environments", {}).items():
            environments[name] = self._parse_environment_config(env_data)
            
        return SystemConfig(
            environment=config_data["environment"],
            services=services,
            environments=environments,
            logging=config_data.get("logging", {}),
            monitoring=config_data.get("monitoring", {}),
            testing=config_data.get("testing", {}),
            deployment=config_data.get("deployment", {})
        )
        
    def _parse_environment_config(self, env_data: Dict[str, Any]) -> EnvironmentConfig:
        """Parse environment configuration from data."""
        backend_data = env_data.get("backend", {})
        frontend_data = env_data.get("frontend", {})
        mobile_data = env_data.get("mobile", {})
        desktop_data = env_data.get("desktop", {})
        infra_data = env_data.get("infrastructure", {})
        
        return EnvironmentConfig(
            name=env_data["name"],
            backend=BackendConfig(**backend_data),
            frontend=FrontendConfig(**frontend_data),
            mobile=MobileConfig(**mobile_data),
            desktop=DesktopConfig(**desktop_data),
            infrastructure=InfrastructureConfig(
                postgres=infra_data.get("postgres", {}),
                redis=infra_data.get("redis", {}),
                minio=infra_data.get("minio", {})
            )
        )
        
    def _write_service_config(self, service_config: ServiceConfig) -> None:
        """Write service-specific configuration file."""
        service_config_path = self.base_config_path / f"{service_config.name}.json"
        
        config_data = {
            "name": service_config.name,
            "type": service_config.type.value,
            "port": service_config.port,
            "health_check_url": service_config.health_check_url,
            "startup_command": service_config.startup_command,
            "environment_variables": service_config.environment_variables,
            "dependencies": service_config.dependencies,
            "working_directory": service_config.working_directory,
            "timeout": service_config.timeout,
            "restart_policy": service_config.restart_policy,
            "max_restarts": service_config.max_restarts
        }
        
        with open(service_config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
            
        logger.info(f"Written configuration for service: {service_config.name}")