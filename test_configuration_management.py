#!/usr/bin/env python3
"""
Test suite for Configuration Management System

Tests the configuration management capabilities including:
- Configuration loading and validation
- Environment-specific configurations
- Configuration propagation
- Hot-reload capabilities
"""

import pytest
import asyncio
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

from orchestration.config.manager import ConfigurationManager
from orchestration.config.models import ServiceConfig, SystemConfig, ServiceType, ValidationResult
from orchestration.config.validator import ConfigValidator


class TestConfigurationManager:
    """Test cases for ConfigurationManager."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary configuration directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def sample_config(self):
        """Sample configuration data."""
        return {
            "environment": "development",
            "services": {
                "test-service": {
                    "name": "test-service",
                    "type": "backend",
                    "port": 8080,
                    "health_check_url": "http://localhost:8080/health",
                    "startup_command": "python app.py",
                    "environment_variables": {"ENV": "test"},
                    "dependencies": []
                }
            },
            "environments": {
                "development": {
                    "name": "development",
                    "backend": {
                        "api_port": 8000,
                        "debug": True
                    }
                }
            }
        }
    
    def test_initialization(self, temp_config_dir):
        """Test ConfigurationManager initialization."""
        config_manager = ConfigurationManager(str(temp_config_dir))
        
        assert config_manager.base_config_path == temp_config_dir
        assert config_manager.validator is not None
        assert config_manager.current_config is None
        assert isinstance(config_manager.config_cache, dict)
        assert isinstance(config_manager.change_callbacks, list)
    
    def test_create_default_config(self, temp_config_dir):
        """Test default configuration creation."""
        config_manager = ConfigurationManager(str(temp_config_dir))
        
        default_config_path = temp_config_dir / "default.yaml"
        assert default_config_path.exists()
        
        # Verify default config content
        with open(default_config_path, 'r') as f:
            config_data = yaml.safe_load(f)
            
        assert config_data['environment'] == 'development'
        assert 'services' in config_data
        assert 'environments' in config_data
        assert 'logging' in config_data
        assert 'monitoring' in config_data
    
    def test_load_system_config(self, temp_config_dir, sample_config):
        """Test system configuration loading."""
        # Create config file
        config_file = temp_config_dir / "test.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(sample_config, f)
        
        config_manager = ConfigurationManager(str(temp_config_dir))
        system_config = config_manager.load_system_config(str(config_file))
        
        assert isinstance(system_config, SystemConfig)
        assert system_config.environment == "development"
        assert "test-service" in system_config.services
        assert system_config.services["test-service"].type == ServiceType.BACKEND
    
    def test_load_environment_config(self, temp_config_dir, sample_config):
        """Test environment-specific configuration loading."""
        # Create config file
        config_file = temp_config_dir / "development.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(sample_config, f)
        
        config_manager = ConfigurationManager(str(temp_config_dir))
        env_config = config_manager.load_environment_config("development")
        
        assert env_config.name == "development"
        assert env_config.backend.api_port == 8000
        assert env_config.backend.debug is True
    
    def test_validate_configuration(self, temp_config_dir, sample_config):
        """Test configuration validation."""
        config_file = temp_config_dir / "test.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(sample_config, f)
        
        config_manager = ConfigurationManager(str(temp_config_dir))
        system_config = config_manager.load_system_config(str(config_file))
        
        validation_result = config_manager.validate_configuration(system_config)
        
        assert isinstance(validation_result, ValidationResult)
        assert validation_result.is_valid
        assert len(validation_result.errors) == 0
    
    def test_propagate_config(self, temp_config_dir, sample_config):
        """Test configuration propagation."""
        config_file = temp_config_dir / "test.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(sample_config, f)
        
        config_manager = ConfigurationManager(str(temp_config_dir))
        system_config = config_manager.load_system_config(str(config_file))
        
        config_manager.propagate_config(["test-service"])
        
        # Check if service config file was created
        service_config_file = temp_config_dir / "test-service.json"
        assert service_config_file.exists()
    
    def test_config_watching_start_stop(self, temp_config_dir):
        """Test configuration file watching."""
        config_manager = ConfigurationManager(str(temp_config_dir))
        
        # Start watching
        config_manager.start_config_watching()
        assert config_manager.observer is not None
        
        # Stop watching
        config_manager.stop_config_watching()
        assert config_manager.observer is None
    
    def test_add_change_callback(self, temp_config_dir):
        """Test adding configuration change callbacks."""
        config_manager = ConfigurationManager(str(temp_config_dir))
        
        callback = MagicMock()
        config_manager.add_change_callback(callback)
        
        assert callback in config_manager.change_callbacks


class TestConfigValidator:
    """Test cases for ConfigValidator."""
    
    @pytest.fixture
    def validator(self):
        """Create ConfigValidator instance."""
        return ConfigValidator()
    
    def test_valid_service_config(self, validator):
        """Test validation of valid service configuration."""
        service_config = ServiceConfig(
            name="test-service",
            type=ServiceType.BACKEND,
            port=8080,
            health_check_url="http://localhost:8080/health",
            startup_command="python app.py"
        )
        
        result = validator.validate_service_config(service_config)
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_invalid_service_config(self, validator):
        """Test validation of invalid service configuration."""
        service_config = ServiceConfig(
            name="",  # Invalid: empty name
            type=ServiceType.BACKEND,
            port=70000,  # Invalid: port out of range
            health_check_url="invalid-url",  # Invalid: malformed URL
            startup_command=""  # Invalid: empty command
        )
        
        result = validator.validate_service_config(service_config)
        
        assert not result.is_valid
        assert len(result.errors) > 0
    
    def test_port_conflict_detection(self, validator):
        """Test port conflict detection."""
        services = {
            "service1": ServiceConfig(
                name="service1",
                type=ServiceType.BACKEND,
                port=8080,
                health_check_url="http://localhost:8080/health",
                startup_command="python app1.py"
            ),
            "service2": ServiceConfig(
                name="service2",
                type=ServiceType.BACKEND,
                port=8080,  # Same port as service1
                health_check_url="http://localhost:8080/health",
                startup_command="python app2.py"
            )
        }
        
        conflicts = validator._check_port_conflicts(services)
        
        assert len(conflicts) == 1
        assert "Port conflict" in conflicts[0]
    
    def test_config_file_validation(self, validator):
        """Test configuration file validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({"test": "data"}, f)
            temp_file = Path(f.name)
        
        try:
            result = validator.validate_config_file(temp_file)
            assert result.is_valid
            assert len(result.errors) == 0
        finally:
            temp_file.unlink()
    
    def test_nonexistent_config_file_validation(self, validator):
        """Test validation of non-existent configuration file."""
        nonexistent_file = Path("/nonexistent/config.yaml")
        
        result = validator.validate_config_file(nonexistent_file)
        
        assert not result.is_valid
        assert len(result.errors) > 0
        assert "does not exist" in result.errors[0]


class TestConfigurationIntegration:
    """Integration tests for configuration management."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary configuration directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.mark.asyncio
    async def test_configuration_hot_reload_simulation(self, temp_config_dir):
        """Test configuration hot-reload simulation."""
        config_manager = ConfigurationManager(str(temp_config_dir))
        
        # Create initial config
        initial_config = {
            "environment": "development",
            "services": {
                "test-service": {
                    "name": "test-service",
                    "type": "backend",
                    "port": 8080,
                    "health_check_url": "http://localhost:8080/health",
                    "startup_command": "python app.py"
                }
            }
        }
        
        config_file = temp_config_dir / "test.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(initial_config, f)
        
        # Load initial config
        system_config = config_manager.load_system_config(str(config_file))
        assert system_config.services["test-service"].port == 8080
        
        # Simulate config change
        updated_config = initial_config.copy()
        updated_config["services"]["test-service"]["port"] = 8081
        
        with open(config_file, 'w') as f:
            yaml.dump(updated_config, f)
        
        # Reload config
        updated_system_config = config_manager.load_system_config(str(config_file))
        assert updated_system_config.services["test-service"].port == 8081
    
    def test_multi_environment_configuration(self, temp_config_dir):
        """Test multi-environment configuration handling."""
        config_manager = ConfigurationManager(str(temp_config_dir))
        
        environments = ["development", "testing", "staging", "production"]
        
        for env in environments:
            env_config = {
                "environment": env,
                "environments": {
                    env: {
                        "name": env,
                        "backend": {
                            "api_port": 8000 + environments.index(env),
                            "debug": env in ["development", "testing"]
                        }
                    }
                }
            }
            
            config_file = temp_config_dir / f"{env}.yaml"
            with open(config_file, 'w') as f:
                yaml.dump(env_config, f)
        
        # Test loading each environment
        for env in environments:
            env_config = config_manager.load_environment_config(env)
            expected_port = 8000 + environments.index(env)
            expected_debug = env in ["development", "testing"]
            
            assert env_config.name == env
            assert env_config.backend.api_port == expected_port
            assert env_config.backend.debug == expected_debug


@pytest.mark.asyncio
async def test_configuration_manager_demo():
    """Test the configuration manager demo functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_manager = ConfigurationManager(temp_dir)
        
        # Test basic functionality
        system_config = config_manager.load_system_config()
        assert system_config is not None
        
        validation_result = config_manager.validate_configuration(system_config)
        assert validation_result is not None
        
        # Test environment loading
        env_config = config_manager.load_environment_config("development")
        assert env_config is not None
        assert env_config.name == "development"


if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"])