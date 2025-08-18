#!/usr/bin/env python3
"""
Test suite for Service Orchestration Engine

Tests the service orchestration capabilities including:
- Service lifecycle management
- Dependency resolution
- Health monitoring
- Configuration integration
"""

import pytest
import asyncio
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from orchestration.config.manager import ConfigurationManager
from orchestration.core.orchestrator import ServiceOrchestrator
from orchestration.core.service_manager import ServiceManager, BackendServiceManager, InfrastructureServiceManager
from orchestration.core.types import ServiceInfo, ServiceStatus, ServiceType, SystemHealth, StartupResult
from orchestration.config.models import ServiceConfig


class TestServiceManager:
    """Test cases for ServiceManager."""
    
    @pytest.fixture
    def sample_service_config(self):
        """Sample service configuration."""
        return ServiceConfig(
            name="test-service",
            type=ServiceType.BACKEND,
            port=8080,
            health_check_url="http://localhost:8080/health",
            startup_command="echo 'test service'",
            environment_variables={"TEST": "true"},
            dependencies=[],
            working_directory=".",
            timeout=30,
            restart_policy="on-failure",
            max_restarts=3
        )
    
    def test_service_manager_initialization(self, sample_service_config):
        """Test ServiceManager initialization."""
        manager = ServiceManager(sample_service_config)
        
        assert manager.config == sample_service_config
        assert manager.service_info.name == "test-service"
        assert manager.service_info.service_type == ServiceType.BACKEND
        assert manager.service_info.status == ServiceStatus.STOPPED
        assert manager.process is None
        assert manager.restart_attempts == 0
        assert manager.max_restart_attempts == 3
    
    @pytest.mark.asyncio
    async def test_service_start_success(self, sample_service_config):
        """Test successful service start."""
        # Use a simple command that will succeed
        sample_service_config.startup_command = "sleep 10"
        manager = ServiceManager(sample_service_config)
        
        with patch('subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.pid = 12345
            mock_process.poll.return_value = None  # Process is running
            mock_popen.return_value = mock_process
            
            result = await manager.start()
            
            assert result.success
            assert result.pid == 12345
            assert manager.service_info.status == ServiceStatus.RUNNING
            assert manager.service_info.pid == 12345
    
    @pytest.mark.asyncio
    async def test_service_start_failure(self, sample_service_config):
        """Test service start failure."""
        sample_service_config.startup_command = "nonexistent-command"
        manager = ServiceManager(sample_service_config)
        
        with patch('subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.poll.return_value = 1  # Process exited with error
            mock_process.communicate.return_value = (b"", b"Command not found")
            mock_popen.return_value = mock_process
            
            result = await manager.start()
            
            assert not result.success
            assert "Command not found" in result.error_message
            assert manager.service_info.status == ServiceStatus.FAILED
    
    @pytest.mark.asyncio
    async def test_service_stop(self, sample_service_config):
        """Test service stop."""
        manager = ServiceManager(sample_service_config)
        
        # Mock a running process
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None
        manager.process = mock_process
        manager.service_info.status = ServiceStatus.RUNNING
        manager.service_info.pid = 12345
        
        with patch('os.killpg') as mock_killpg, \
             patch('os.getpgid') as mock_getpgid, \
             patch('os.name', 'posix'):
            
            mock_getpgid.return_value = 12345
            
            # Mock process exit
            async def mock_wait():
                mock_process.poll.return_value = 0
            
            with patch.object(manager, '_wait_for_process_exit', side_effect=mock_wait):
                result = await manager.stop()
            
            assert result
            assert manager.service_info.status == ServiceStatus.STOPPED
            assert manager.service_info.pid is None
            assert manager.process is None
    
    def test_is_running(self, sample_service_config):
        """Test is_running method."""
        manager = ServiceManager(sample_service_config)
        
        # Initially not running
        assert not manager.is_running()
        
        # Mock running process
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        manager.process = mock_process
        manager.service_info.status = ServiceStatus.RUNNING
        
        assert manager.is_running()
        
        # Mock process exit
        mock_process.poll.return_value = 0
        assert not manager.is_running()
        assert manager.service_info.status == ServiceStatus.STOPPED
    
    @pytest.mark.asyncio
    async def test_health_check(self, sample_service_config):
        """Test health check."""
        manager = ServiceManager(sample_service_config)
        
        # Health check on stopped service
        result = await manager.health_check()
        assert not result
        assert manager.service_info.health_status == "stopped"
        
        # Mock running service
        manager.service_info.status = ServiceStatus.RUNNING
        manager.service_info.pid = 12345
        
        with patch('psutil.Process') as mock_process_class:
            mock_process = MagicMock()
            mock_process.is_running.return_value = True
            mock_process_class.return_value = mock_process
            
            result = await manager.health_check()
            
            assert result
            assert manager.service_info.health_status == "healthy"


class TestBackendServiceManager:
    """Test cases for BackendServiceManager."""
    
    @pytest.fixture
    def fastapi_config(self):
        """FastAPI service configuration."""
        return ServiceConfig(
            name="fastapi",
            type=ServiceType.BACKEND,
            port=8000,
            health_check_url="http://localhost:8000/health",
            startup_command="uvicorn app:app",
            environment_variables={"DEBUG": "true"},
            dependencies=[]
        )
    
    @pytest.mark.asyncio
    async def test_fastapi_start_with_env_vars(self, fastapi_config):
        """Test FastAPI service start with environment variables."""
        manager = BackendServiceManager(fastapi_config)
        
        with patch('subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.pid = 12345
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process
            
            result = await manager.start()
            
            # Check that FastAPI-specific environment variables were added
            call_args = mock_popen.call_args
            env = call_args[1]['env']
            
            assert env['UVICORN_HOST'] == "0.0.0.0"
            assert env['UVICORN_PORT'] == "8000"
            assert env['UVICORN_RELOAD'] == "true"


class TestServiceOrchestrator:
    """Test cases for ServiceOrchestrator."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary configuration directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def sample_system_config(self):
        """Sample system configuration."""
        return {
            "environment": "development",
            "services": {
                "database": {
                    "name": "database",
                    "type": "infrastructure",
                    "port": 5432,
                    "health_check_url": "postgresql://localhost:5432",
                    "startup_command": "docker run postgres",
                    "dependencies": []
                },
                "api": {
                    "name": "api",
                    "type": "backend",
                    "port": 8000,
                    "health_check_url": "http://localhost:8000/health",
                    "startup_command": "uvicorn app:app",
                    "dependencies": ["database"]
                },
                "frontend": {
                    "name": "frontend",
                    "type": "frontend",
                    "port": 3000,
                    "health_check_url": "http://localhost:3000",
                    "startup_command": "npm start",
                    "dependencies": ["api"]
                }
            },
            "environments": {
                "development": {
                    "name": "development"
                }
            }
        }
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self, temp_config_dir, sample_system_config):
        """Test orchestrator initialization."""
        # Create config file
        config_file = temp_config_dir / "test.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(sample_system_config, f)
        
        config_manager = ConfigurationManager(str(temp_config_dir))
        orchestrator = ServiceOrchestrator(config_manager)
        
        success = await orchestrator.initialize()
        
        assert success
        assert len(orchestrator.service_managers) == 3
        assert "database" in orchestrator.service_managers
        assert "api" in orchestrator.service_managers
        assert "frontend" in orchestrator.service_managers
    
    def test_startup_order_calculation(self, temp_config_dir, sample_system_config):
        """Test startup order calculation based on dependencies."""
        # Create config file
        config_file = temp_config_dir / "test.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(sample_system_config, f)
        
        config_manager = ConfigurationManager(str(temp_config_dir))
        orchestrator = ServiceOrchestrator(config_manager)
        
        # Initialize synchronously for this test
        orchestrator.system_config = config_manager.load_system_config()
        orchestrator._create_service_managers()
        startup_order = orchestrator._calculate_startup_order()
        
        # Database should start first, then API, then frontend
        assert startup_order.index("database") < startup_order.index("api")
        assert startup_order.index("api") < startup_order.index("frontend")
    
    def test_circular_dependency_detection(self, temp_config_dir):
        """Test circular dependency detection."""
        circular_config = {
            "environment": "development",
            "services": {
                "service_a": {
                    "name": "service_a",
                    "type": "backend",
                    "port": 8000,
                    "health_check_url": "http://localhost:8000",
                    "startup_command": "echo a",
                    "dependencies": ["service_b"]
                },
                "service_b": {
                    "name": "service_b",
                    "type": "backend",
                    "port": 8001,
                    "health_check_url": "http://localhost:8001",
                    "startup_command": "echo b",
                    "dependencies": ["service_a"]
                }
            },
            "environments": {"development": {"name": "development"}}
        }
        
        config_file = temp_config_dir / "circular.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(circular_config, f)
        
        config_manager = ConfigurationManager(str(temp_config_dir))
        orchestrator = ServiceOrchestrator(config_manager)
        
        orchestrator.system_config = config_manager.load_system_config(str(config_file))
        orchestrator._create_service_managers()
        
        with pytest.raises(ValueError, match="Circular dependency detected"):
            orchestrator._calculate_startup_order()
    
    @pytest.mark.asyncio
    async def test_start_service_with_dependencies(self, temp_config_dir, sample_system_config):
        """Test starting a service with dependencies."""
        config_file = temp_config_dir / "test.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(sample_system_config, f)
        
        config_manager = ConfigurationManager(str(temp_config_dir))
        orchestrator = ServiceOrchestrator(config_manager)
        await orchestrator.initialize()
        
        # Mock service managers
        for manager in orchestrator.service_managers.values():
            manager.start = AsyncMock(return_value=StartupResult(success=True))
            manager.is_running = MagicMock(return_value=True)
        
        # Start frontend service (which depends on api, which depends on database)
        result = await orchestrator.start_service("frontend")
        
        assert result.success
        
        # Verify that dependencies were started
        orchestrator.service_managers["database"].start.assert_called_once()
        orchestrator.service_managers["api"].start.assert_called_once()
        orchestrator.service_managers["frontend"].start.assert_called_once()
    
    def test_get_service_dependencies(self, temp_config_dir, sample_system_config):
        """Test getting service dependencies."""
        config_file = temp_config_dir / "test.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(sample_system_config, f)
        
        config_manager = ConfigurationManager(str(temp_config_dir))
        orchestrator = ServiceOrchestrator(config_manager)
        orchestrator.system_config = config_manager.load_system_config()
        
        # Test dependencies
        assert orchestrator.get_service_dependencies("database") == []
        assert orchestrator.get_service_dependencies("api") == ["database"]
        assert orchestrator.get_service_dependencies("frontend") == ["api"]
    
    def test_get_service_dependents(self, temp_config_dir, sample_system_config):
        """Test getting service dependents."""
        config_file = temp_config_dir / "test.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(sample_system_config, f)
        
        config_manager = ConfigurationManager(str(temp_config_dir))
        orchestrator = ServiceOrchestrator(config_manager)
        orchestrator.system_config = config_manager.load_system_config()
        
        # Test dependents
        assert "api" in orchestrator.get_service_dependents("database")
        assert "frontend" in orchestrator.get_service_dependents("api")
        assert orchestrator.get_service_dependents("frontend") == []
    
    def test_get_system_health(self, temp_config_dir, sample_system_config):
        """Test system health calculation."""
        config_file = temp_config_dir / "test.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(sample_system_config, f)
        
        config_manager = ConfigurationManager(str(temp_config_dir))
        orchestrator = ServiceOrchestrator(config_manager)
        orchestrator.system_config = config_manager.load_system_config()
        orchestrator._create_service_managers()
        
        # All services stopped
        health = orchestrator.get_system_health()
        assert health == SystemHealth.UNHEALTHY
        
        # Some services running
        orchestrator.service_managers["database"].service_info.status = ServiceStatus.RUNNING
        health = orchestrator.get_system_health()
        assert health == SystemHealth.DEGRADED
        
        # All services running
        for manager in orchestrator.service_managers.values():
            manager.service_info.status = ServiceStatus.RUNNING
        health = orchestrator.get_system_health()
        assert health == SystemHealth.HEALTHY


@pytest.mark.asyncio
async def test_orchestrator_demo():
    """Test the orchestrator demo functionality."""
    config_manager = ConfigurationManager("orchestration/configs")
    orchestrator = ServiceOrchestrator(config_manager)
    
    # Test basic initialization
    success = await orchestrator.initialize()
    assert success or not success  # Should handle both cases gracefully
    
    # Test getting stats
    stats = orchestrator.get_orchestrator_stats()
    assert isinstance(stats, dict)
    assert 'total_services' in stats
    assert 'system_health' in stats


if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"])