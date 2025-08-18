"""Configuration validation utilities."""

import re
from typing import Dict, Any, List
from pathlib import Path
from .models import ValidationResult, ServiceConfig, SystemConfig, ServiceType


class ConfigValidator:
    """Validates configuration files and objects."""
    
    def __init__(self):
        self.required_fields = {
            'service': ['name', 'type', 'port', 'health_check_url', 'startup_command'],
            'environment': ['name'],
            'system': ['environment']
        }
        
    def validate_system_config(self, config: SystemConfig) -> ValidationResult:
        """Validate complete system configuration."""
        errors = []
        warnings = []
        
        # Validate environment exists
        if not config.environment:
            errors.append("System environment must be specified")
        elif config.environment not in config.environments:
            errors.append(f"Environment '{config.environment}' not found in environments configuration")
            
        # Validate services
        for service_name, service_config in config.services.items():
            service_result = self.validate_service_config(service_config)
            if not service_result.is_valid:
                errors.extend([f"Service '{service_name}': {error}" for error in service_result.errors])
            warnings.extend([f"Service '{service_name}': {warning}" for warning in service_result.warnings])
            
        # Check for port conflicts
        port_conflicts = self._check_port_conflicts(config.services)
        if port_conflicts:
            errors.extend(port_conflicts)
            
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
        
    def validate_service_config(self, config: ServiceConfig) -> ValidationResult:
        """Validate individual service configuration."""
        errors = []
        warnings = []
        
        # Check required fields
        if not config.name:
            errors.append("Service name is required")
        elif not re.match(r'^[a-zA-Z0-9_-]+$', config.name):
            errors.append("Service name must contain only alphanumeric characters, hyphens, and underscores")
            
        if not isinstance(config.type, ServiceType):
            errors.append("Service type must be a valid ServiceType enum value")
            
        if not isinstance(config.port, int) or config.port <= 0 or config.port > 65535:
            errors.append("Service port must be a valid integer between 1 and 65535")
            
        if not config.health_check_url:
            errors.append("Health check URL is required")
        elif not self._is_valid_url(config.health_check_url):
            warnings.append("Health check URL format may be invalid")
            
        if not config.startup_command:
            errors.append("Startup command is required")
            
        # Validate timeout
        if config.timeout <= 0:
            errors.append("Timeout must be a positive integer")
        elif config.timeout < 5:
            warnings.append("Timeout less than 5 seconds may cause issues")
            
        # Validate max_restarts
        if config.max_restarts < 0:
            errors.append("Max restarts must be non-negative")
            
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
        
    def validate_config_file(self, file_path: Path) -> ValidationResult:
        """Validate configuration file exists and is readable."""
        errors = []
        warnings = []
        
        if not file_path.exists():
            errors.append(f"Configuration file does not exist: {file_path}")
            return ValidationResult(is_valid=False, errors=errors)
            
        if not file_path.is_file():
            errors.append(f"Configuration path is not a file: {file_path}")
            return ValidationResult(is_valid=False, errors=errors)
            
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                if not content.strip():
                    warnings.append(f"Configuration file is empty: {file_path}")
        except PermissionError:
            errors.append(f"Permission denied reading configuration file: {file_path}")
        except Exception as e:
            errors.append(f"Error reading configuration file {file_path}: {str(e)}")
            
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
        
    def _check_port_conflicts(self, services: Dict[str, ServiceConfig]) -> List[str]:
        """Check for port conflicts between services."""
        port_map = {}
        conflicts = []
        
        for service_name, service_config in services.items():
            port = service_config.port
            if port in port_map:
                conflicts.append(
                    f"Port conflict: Services '{port_map[port]}' and '{service_name}' "
                    f"both use port {port}"
                )
            else:
                port_map[port] = service_name
                
        return conflicts
        
    def _is_valid_url(self, url: str) -> bool:
        """Basic URL validation."""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(url) is not None