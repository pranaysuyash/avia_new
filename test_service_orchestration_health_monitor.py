#!/usr/bin/env python3
"""
Test suite for the Service Orchestration and Health Monitoring system.

Tests the integrated system that can start services and perform health validation.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Add orchestration to path
import sys
sys.path.append('.')

from orchestration.config.models import (
    SystemConfig, ServiceConfig, ServiceType, EnvironmentConfig,
    BackendConfig, FrontendConfig, InfrastructureConfig
)
from orchestration.config.manager import ConfigurationManager
from orchestration.monitoring.service_orchestration_health_monitor import (
    ServiceOrchestrationHealthMonitor, ServiceStartupStatus, ServiceStartupResult, SystemStartupResult
)
from orchestration.monitoring.health import HealthStatus, HealthCheckResult
from orchestration.core.orchestrator import ServiceOrchestrator
from orchestration.core.types import StartupResult


@pytest.fixture
def sample_config():
    """Create a sample system configuration for testing."""
    services = {
        "database": ServiceConfig(
            name="database",
            type=ServiceType.INFRASTRUCTURE,
            port=5432,
            health_check_url="postgresql://localhost:5432",
            startup_command="pg_ctl start",
            timeout=15,
            dependencies=[]
        ),
        "cache": ServiceConfig(
            name="cache",
            type=ServiceType.INFRASTRUCTURE,
            port=6379,
            health_check_url="redis://localhost:6379",
            startup_command="redis-server",
            timeout=10,
            dependencies=[]
        ),
        "api": ServiceConfig(
            name="api",
            type=ServiceType.BACKEND,
            port=8000,
            health_check_url="http://localhost:8000/health",
            startup_command="uvicorn api.main:app",
            timeout=20,
            dependencies=["database", "cache"]
        ),
        "frontend": ServiceConfig(
            name="frontend",
            type=ServiceType.FRONTEND,
            port=3000,
            health_check_url="http://localhost:3000",
            startup_command="npm start",
            timeout=30,
            dependencies=["api"]
        )
    }
    
    env_config = EnvironmentConfig(
        name="test",
        backend=BackendConfig(api_port=8000),
        frontend=FrontendConfig(port=3000),
        infrastructure=InfrastructureConfig(
            postgres={"host": "localhost", "port": 5432, "database": "test"},
            redis={"host": "localhost", "port": 6379}
        )
    )
    
    return SystemConfig(
        environment="test",
        services=services,
        environments={"test": env_config}
    )


@pytest.fixture
def mock_config_manager(sample_config):
    """Create a mock configuration manager."""
    config_manager = Mock(spec=ConfigurationManager)
    config_manager.load_system_config.return_value = sample_config
    config_manager.validate_configuration.return_value = Mock(is_valid=True, errors=[])
    return config_manager


class TestServiceOrchestrationHealthMonitor:
    """Test the main ServiceOrchestrationHealthMonitor class."""
    
    @pytest.mark.asyncio
    async def test_initialization_success(self, mock_config_manager):
        """Test successful initialization."""
        orchestration_monitor = ServiceOrchestrationHealthMonitor(mock_config_manager)
        
        # Mock orchestrator initialization
        with patch('orchestration.monitoring.service_orchestration_health_monitor.ServiceOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.initialize.return_value = True
            mock_orchestrator.startup_order = ["database", "cache", "api", "frontend"]
            mock_orchestrator_class.return_value = mock_orchestrator
            
            # Mock health monitor
            with patch('orchestration.monitoring.service_orchestration_health_monitor.HealthMonitor') as mock_health_monitor_class:
                mock_health_monitor = Mock()
                mock_health_monitor_class.return_value = mock_health_monitor
                
                success = await orchestration_monitor.initialize()
                
                assert success is True
                assert orchestration_monitor.system_config is not None
                assert orchestration_monitor.orchestrator is not None
                assert orchestration_monitor.health_monitor is not None
                assert len(orchestration_monitor.service_startup_status) == 4
                assert orchestration_monitor.startup_order == ["database", "cache", "api", "frontend"]
    
    @pytest.mark.asyncio
    async def test_initialization_failure_invalid_config(self, mock_config_manager):
        """Test initialization failure due to invalid configuration."""
        # Make config validation fail
        mock_config_manager.validate_configuration.return_value = Mock(
            is_valid=False, 
            errors=["Invalid service configuration"]
        )
        
        orchestration_monitor = ServiceOrchestrationHealthMonitor(mock_config_manager)
        success = await orchestration_monitor.initialize()
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_initialization_failure_orchestrator_init(self, mock_config_manager):
        """Test initialization failure due to orchestrator initialization failure."""
        orchestration_monitor = ServiceOrchestrationHealthMonitor(mock_config_manager)
        
        # Mock orchestrator initialization failure
        with patch('orchestration.monitoring.service_orchestration_health_monitor.ServiceOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.initialize.return_value = False
            mock_orchestrator_class.return_value = mock_orchestrator
            
            success = await orchestration_monitor.initialize()
            
            assert success is False
    
    @pytest.mark.asyncio
    async def test_start_all_services_success(self, mock_config_manager, sample_config):
        """Test successful startup of all services."""
        orchestration_monitor = ServiceOrchestrationHealthMonitor(mock_config_manager)
        
        # Initialize the monitor
        with patch('orchestration.monitoring.service_orchestration_health_monitor.ServiceOrchestrator') as mock_orchestrator_class, \
             patch('orchestration.monitoring.service_orchestration_health_monitor.HealthMonitor') as mock_health_monitor_class:
            
            mock_orchestrator = AsyncMock()
            mock_orchestrator.initialize.return_value = True
            mock_orchestrator.startup_order = ["database", "cache", "api", "frontend"]
            mock_orchestrator_class.return_value = mock_orchestrator
            
            mock_health_monitor = Mock()
            mock_health_monitor.start_monitoring = AsyncMock()
            mock_health_monitor.check_all_services = AsyncMock()
            mock_health_monitor.check_service_connectivity = AsyncMock(return_value=[])
            mock_health_monitor_class.return_value = mock_health_monitor
            
            await orchestration_monitor.initialize()
            
            # Mock service startup and health checks
            mock_orchestrator.start_service = AsyncMock(return_value=StartupResult(success=True))
            mock_health_monitor.check_specific_service = AsyncMock(return_value=HealthCheckResult(
                service_name="test",
                status=HealthStatus.HEALTHY,
                response_time_ms=10.0,
                timestamp=datetime.utcnow().isoformat()
            ))
            
            # Mock comprehensive health check
            from orchestration.monitoring.health import SystemHealth
            mock_system_health = SystemHealth(
                overall_status=HealthStatus.HEALTHY,
                healthy_services=4,
                total_services=4,
                timestamp=datetime.utcnow().isoformat(),
                service_results=[]
            )
            mock_health_monitor.check_all_services.return_value = mock_system_health
            
            # Start all services
            result = await orchestration_monitor.start_all_services_with_health_monitoring()
            
            assert isinstance(result, SystemStartupResult)
            assert result.overall_status == ServiceStartupStatus.HEALTHY
            assert result.successful_services == 4
            assert result.failed_services == 0
            assert len(result.service_results) == 4
    
    @pytest.mark.asyncio
    async def test_start_service_with_dependencies(self, mock_config_manager, sample_config):
        """Test starting a service with dependencies."""
        orchestration_monitor = ServiceOrchestrationHealthMonitor(mock_config_manager)
        
        # Initialize the monitor
        with patch('orchestration.monitoring.service_orchestration_health_monitor.ServiceOrchestrator') as mock_orchestrator_class, \
             patch('orchestration.monitoring.service_orchestration_health_monitor.HealthMonitor') as mock_health_monitor_class:
            
            mock_orchestrator = AsyncMock()
            mock_orchestrator.initialize.return_value = True
            mock_orchestrator.startup_order = ["database", "cache", "api", "frontend"]
            mock_orchestrator_class.return_value = mock_orchestrator
            
            mock_health_monitor = Mock()
            mock_health_monitor_class.return_value = mock_health_monitor
            
            await orchestration_monitor.initialize()
            
            # Mock successful service startup
            mock_orchestrator.start_service = AsyncMock(return_value=StartupResult(success=True))
            
            # Mock health check
            mock_health_monitor.check_specific_service = AsyncMock(return_value=HealthCheckResult(
                service_name="api",
                status=HealthStatus.HEALTHY,
                response_time_ms=15.0,
                timestamp=datetime.utcnow().isoformat()
            ))
            
            # Start API service (which has dependencies)
            result = await orchestration_monitor._start_service_with_health_check("api")
            
            assert isinstance(result, ServiceStartupResult)
            assert result.service_name == "api"
            assert result.status == ServiceStartupStatus.HEALTHY
            assert result.health_check_result is not None
    
    @pytest.mark.asyncio
    async def test_start_service_failure(self, mock_config_manager, sample_config):
        """Test service startup failure."""
        orchestration_monitor = ServiceOrchestrationHealthMonitor(mock_config_manager)
        
        # Initialize the monitor
        with patch('orchestration.monitoring.service_orchestration_health_monitor.ServiceOrchestrator') as mock_orchestrator_class, \
             patch('orchestration.monitoring.service_orchestration_health_monitor.HealthMonitor') as mock_health_monitor_class:
            
            mock_orchestrator = AsyncMock()
            mock_orchestrator.initialize.return_value = True
            mock_orchestrator.startup_order = ["database"]
            mock_orchestrator_class.return_value = mock_orchestrator
            
            mock_health_monitor = Mock()
            mock_health_monitor_class.return_value = mock_health_monitor
            
            await orchestration_monitor.initialize()
            
            # Mock failed service startup
            mock_orchestrator.start_service = AsyncMock(return_value=StartupResult(
                success=False, 
                error_message="Service failed to start"
            ))
            
            # Start service
            result = await orchestration_monitor._start_service_with_health_check("database")
            
            assert isinstance(result, ServiceStartupResult)
            assert result.service_name == "database"
            assert result.status == ServiceStartupStatus.FAILED
            assert result.error_message == "Service failed to start"
    
    @pytest.mark.asyncio
    async def test_health_check_with_retries(self, mock_config_manager, sample_config):
        """Test health check with retry logic."""
        orchestration_monitor = ServiceOrchestrationHealthMonitor(mock_config_manager)
        orchestration_monitor.health_check_retries = 2
        
        # Initialize the monitor
        with patch('orchestration.monitoring.service_orchestration_health_monitor.HealthMonitor') as mock_health_monitor_class:
            mock_health_monitor = Mock()
            mock_health_monitor_class.return_value = mock_health_monitor
            
            orchestration_monitor.health_monitor = mock_health_monitor
            
            # Mock health check that fails first time, succeeds second time
            health_results = [
                HealthCheckResult(
                    service_name="test",
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=5.0,
                    timestamp=datetime.utcnow().isoformat(),
                    error_message="Service not ready"
                ),
                HealthCheckResult(
                    service_name="test",
                    status=HealthStatus.HEALTHY,
                    response_time_ms=10.0,
                    timestamp=datetime.utcnow().isoformat()
                )
            ]
            
            mock_health_monitor.check_specific_service = AsyncMock(side_effect=health_results)
            
            # Perform health check
            result = await orchestration_monitor._perform_service_health_check("test")
            
            assert result is not None
            assert result.status == HealthStatus.HEALTHY
            assert mock_health_monitor.check_specific_service.call_count == 2
    
    @pytest.mark.asyncio
    async def test_comprehensive_health_check(self, mock_config_manager, sample_config):
        """Test comprehensive system health check."""
        orchestration_monitor = ServiceOrchestrationHealthMonitor(mock_config_manager)
        
        # Initialize the monitor
        with patch('orchestration.monitoring.service_orchestration_health_monitor.HealthMonitor') as mock_health_monitor_class:
            mock_health_monitor = Mock()
            mock_health_monitor_class.return_value = mock_health_monitor
            
            orchestration_monitor.health_monitor = mock_health_monitor
            
            # Mock system health check
            from orchestration.monitoring.health import SystemHealth
            mock_system_health = SystemHealth(
                overall_status=HealthStatus.HEALTHY,
                healthy_services=3,
                total_services=4,
                timestamp=datetime.utcnow().isoformat(),
                service_results=[]
            )
            
            mock_health_monitor.check_all_services = AsyncMock(return_value=mock_system_health)
            mock_health_monitor.check_service_connectivity = AsyncMock(return_value=[])
            
            # Perform comprehensive health check
            result = await orchestration_monitor._perform_comprehensive_health_check()
            
            assert result is not None
            assert result.overall_status == HealthStatus.HEALTHY
            assert result.healthy_services == 3
            assert result.total_services == 4
    
    @pytest.mark.asyncio
    async def test_stop_all_services(self, mock_config_manager, sample_config):
        """Test stopping all services."""
        orchestration_monitor = ServiceOrchestrationHealthMonitor(mock_config_manager)
        
        # Initialize the monitor
        with patch('orchestration.monitoring.service_orchestration_health_monitor.ServiceOrchestrator') as mock_orchestrator_class, \
             patch('orchestration.monitoring.service_orchestration_health_monitor.HealthMonitor') as mock_health_monitor_class:
            
            mock_orchestrator = AsyncMock()
            mock_orchestrator.initialize.return_value = True
            mock_orchestrator.stop_all_services = AsyncMock(return_value={
                "database": True,
                "cache": True,
                "api": False,
                "frontend": True
            })
            mock_orchestrator_class.return_value = mock_orchestrator
            
            mock_health_monitor = Mock()
            mock_health_monitor.running = True
            mock_health_monitor.stop_monitoring = AsyncMock()
            mock_health_monitor_class.return_value = mock_health_monitor
            
            await orchestration_monitor.initialize()
            
            # Stop all services
            results = await orchestration_monitor.stop_all_services()
            
            assert results["database"] is True
            assert results["cache"] is True
            assert results["api"] is False
            assert results["frontend"] is True
            assert orchestration_monitor.system_started is False
            mock_health_monitor.stop_monitoring.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_restart_service_with_health_check(self, mock_config_manager, sample_config):
        """Test restarting a service with health verification."""
        orchestration_monitor = ServiceOrchestrationHealthMonitor(mock_config_manager)
        
        # Initialize the monitor
        with patch('orchestration.monitoring.service_orchestration_health_monitor.ServiceOrchestrator') as mock_orchestrator_class, \
             patch('orchestration.monitoring.service_orchestration_health_monitor.HealthMonitor') as mock_health_monitor_class:
            
            mock_orchestrator = AsyncMock()
            mock_orchestrator.initialize.return_value = True
            mock_orchestrator.stop_service = AsyncMock(return_value=True)
            mock_orchestrator.start_service = AsyncMock(return_value=StartupResult(success=True))
            mock_orchestrator_class.return_value = mock_orchestrator
            
            mock_health_monitor = Mock()
            mock_health_monitor.check_specific_service = AsyncMock(return_value=HealthCheckResult(
                service_name="api",
                status=HealthStatus.HEALTHY,
                response_time_ms=12.0,
                timestamp=datetime.utcnow().isoformat()
            ))
            mock_health_monitor_class.return_value = mock_health_monitor
            
            await orchestration_monitor.initialize()
            
            # Restart service
            result = await orchestration_monitor.restart_service_with_health_check("api")
            
            assert isinstance(result, ServiceStartupResult)
            assert result.service_name == "api"
            assert result.status == ServiceStartupStatus.HEALTHY
            mock_orchestrator.stop_service.assert_called_once_with("api")
    
    def test_get_service_startup_status(self, mock_config_manager, sample_config):
        """Test getting service startup status."""
        orchestration_monitor = ServiceOrchestrationHealthMonitor(mock_config_manager)
        orchestration_monitor.system_config = sample_config
        
        # Set some service statuses
        orchestration_monitor.service_startup_status["database"] = ServiceStartupStatus.HEALTHY
        orchestration_monitor.service_startup_status["api"] = ServiceStartupStatus.FAILED
        
        # Test individual service status
        assert orchestration_monitor.get_service_startup_status("database") == ServiceStartupStatus.HEALTHY
        assert orchestration_monitor.get_service_startup_status("api") == ServiceStartupStatus.FAILED
        assert orchestration_monitor.get_service_startup_status("nonexistent") is None
        
        # Test all service statuses
        all_statuses = orchestration_monitor.get_all_service_startup_status()
        assert all_statuses["database"] == ServiceStartupStatus.HEALTHY
        assert all_statuses["api"] == ServiceStartupStatus.FAILED
    
    @pytest.mark.asyncio
    async def test_get_current_system_status(self, mock_config_manager, sample_config):
        """Test getting current system status."""
        orchestration_monitor = ServiceOrchestrationHealthMonitor(mock_config_manager)
        
        # Initialize the monitor
        with patch('orchestration.monitoring.service_orchestration_health_monitor.HealthMonitor') as mock_health_monitor_class:
            mock_health_monitor = Mock()
            mock_health_monitor.get_health_monitor_status.return_value = {
                "running": True,
                "check_interval": 30,
                "total_checks_configured": 4
            }
            mock_health_monitor.check_specific_service = AsyncMock(return_value=HealthCheckResult(
                service_name="test",
                status=HealthStatus.HEALTHY,
                response_time_ms=8.0,
                timestamp=datetime.utcnow().isoformat()
            ))
            mock_health_monitor.check_all_services = AsyncMock()
            mock_health_monitor_class.return_value = mock_health_monitor
            
            orchestration_monitor.health_monitor = mock_health_monitor
            orchestration_monitor.system_config = sample_config
            orchestration_monitor.system_started = True
            orchestration_monitor.service_startup_status = {
                "database": ServiceStartupStatus.HEALTHY,
                "api": ServiceStartupStatus.FAILED
            }
            orchestration_monitor.service_startup_times = {
                "database": 1500.0,
                "api": 2000.0
            }
            
            # Get current system status
            status = await orchestration_monitor.get_current_system_status()
            
            assert status["system_started"] is True
            assert status["startup_in_progress"] is False
            assert "timestamp" in status
            assert "services" in status
            assert "health_monitor" in status
            
            # Check service details
            assert status["services"]["database"]["startup_status"] == "healthy"
            assert status["services"]["database"]["startup_time_ms"] == 1500.0
            assert status["services"]["api"]["startup_status"] == "failed"
    
    @pytest.mark.asyncio
    async def test_validate_system_readiness(self, mock_config_manager, sample_config):
        """Test system readiness validation."""
        orchestration_monitor = ServiceOrchestrationHealthMonitor(mock_config_manager)
        
        # Initialize the monitor
        with patch('orchestration.monitoring.service_orchestration_health_monitor.HealthMonitor') as mock_health_monitor_class:
            mock_health_monitor = Mock()
            mock_health_monitor.running = True
            mock_health_monitor._get_total_checks.return_value = 4
            mock_health_monitor.health_history = [Mock()]  # Non-empty history
            mock_health_monitor_class.return_value = mock_health_monitor
            
            orchestration_monitor.health_monitor = mock_health_monitor
            orchestration_monitor.system_config = sample_config
            orchestration_monitor.service_startup_status = {
                "database": ServiceStartupStatus.HEALTHY,
                "cache": ServiceStartupStatus.HEALTHY,
                "api": ServiceStartupStatus.STARTED,
                "frontend": ServiceStartupStatus.FAILED
            }
            
            # Validate system readiness
            validation = await orchestration_monitor.validate_system_readiness()
            
            assert "ready" in validation
            assert "checks" in validation
            assert "configuration" in validation["checks"]
            assert "services" in validation["checks"]
            assert "health_monitoring" in validation["checks"]
            
            # Configuration should be valid
            assert validation["checks"]["configuration"]["valid"] is True
            
            # Not all services are ready (frontend failed)
            assert validation["checks"]["services"]["all_services_started"] is False
            
            # Health monitoring should be ready
            assert validation["checks"]["health_monitoring"]["monitor_running"] is True


class TestServiceStartupResult:
    """Test ServiceStartupResult data class."""
    
    def test_service_startup_result_creation(self):
        """Test creating ServiceStartupResult."""
        health_result = HealthCheckResult(
            service_name="test",
            status=HealthStatus.HEALTHY,
            response_time_ms=10.0,
            timestamp=datetime.utcnow().isoformat()
        )
        
        result = ServiceStartupResult(
            service_name="test_service",
            status=ServiceStartupStatus.HEALTHY,
            startup_time_ms=1500.0,
            health_check_result=health_result,
            dependencies_started=["dep1", "dep2"]
        )
        
        assert result.service_name == "test_service"
        assert result.status == ServiceStartupStatus.HEALTHY
        assert result.startup_time_ms == 1500.0
        assert result.health_check_result == health_result
        assert result.dependencies_started == ["dep1", "dep2"]
    
    def test_service_startup_result_to_dict(self):
        """Test converting ServiceStartupResult to dictionary."""
        health_result = HealthCheckResult(
            service_name="test",
            status=HealthStatus.HEALTHY,
            response_time_ms=10.0,
            timestamp=datetime.utcnow().isoformat()
        )
        
        result = ServiceStartupResult(
            service_name="test_service",
            status=ServiceStartupStatus.HEALTHY,
            startup_time_ms=1500.0,
            health_check_result=health_result
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["service_name"] == "test_service"
        assert result_dict["status"] == "healthy"
        assert result_dict["startup_time_ms"] == 1500.0
        assert result_dict["health_check_result"] is not None
        assert result_dict["dependencies_started"] == []


class TestSystemStartupResult:
    """Test SystemStartupResult data class."""
    
    def test_system_startup_result_creation(self):
        """Test creating SystemStartupResult."""
        service_results = [
            ServiceStartupResult(
                service_name="service1",
                status=ServiceStartupStatus.HEALTHY,
                startup_time_ms=1000.0,
                health_check_result=None
            )
        ]
        
        result = SystemStartupResult(
            overall_status=ServiceStartupStatus.HEALTHY,
            total_services=1,
            successful_services=1,
            failed_services=0,
            startup_time_ms=2000.0,
            service_results=service_results,
            system_health=None
        )
        
        assert result.overall_status == ServiceStartupStatus.HEALTHY
        assert result.total_services == 1
        assert result.successful_services == 1
        assert result.failed_services == 0
        assert result.startup_time_ms == 2000.0
        assert len(result.service_results) == 1
    
    def test_system_startup_result_to_dict(self):
        """Test converting SystemStartupResult to dictionary."""
        service_results = [
            ServiceStartupResult(
                service_name="service1",
                status=ServiceStartupStatus.HEALTHY,
                startup_time_ms=1000.0,
                health_check_result=None
            )
        ]
        
        result = SystemStartupResult(
            overall_status=ServiceStartupStatus.HEALTHY,
            total_services=1,
            successful_services=1,
            failed_services=0,
            startup_time_ms=2000.0,
            service_results=service_results,
            system_health=None
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["overall_status"] == "healthy"
        assert result_dict["total_services"] == 1
        assert result_dict["successful_services"] == 1
        assert result_dict["failed_services"] == 0
        assert result_dict["startup_time_ms"] == 2000.0
        assert len(result_dict["service_results"]) == 1
        assert result_dict["system_health"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])