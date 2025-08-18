#!/usr/bin/env python3
"""
Comprehensive test suite for the enhanced health monitoring system.

Tests cover:
- HTTP service health checks
- Database connectivity and performance checks
- Cache (Redis) health monitoring
- Storage (MinIO) health checks
- Frontend application health verification
- Service-to-service connectivity testing
- Health check endpoints
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Add orchestration to path
import sys
sys.path.append('.')

from orchestration.config.models import (
    SystemConfig, ServiceConfig, ServiceType, EnvironmentConfig,
    BackendConfig, FrontendConfig, InfrastructureConfig
)
from orchestration.monitoring.health import (
    HealthMonitor, HealthStatus, ServiceHealthCheck, DatabaseHealthCheck,
    CacheHealthCheck, StorageHealthCheck, FrontendHealthCheck,
    ConnectivityHealthCheck, HealthCheckResult
)
from orchestration.monitoring.endpoints import HealthEndpoints, StreamlitHealthEndpoints


@pytest.fixture
def sample_config():
    """Create a sample system configuration for testing."""
    services = {
        "fastapi": ServiceConfig(
            name="fastapi",
            type=ServiceType.BACKEND,
            port=8000,
            health_check_url="http://localhost:8000/health",
            startup_command="uvicorn api.main:app",
            timeout=10
        ),
        "streamlit": ServiceConfig(
            name="streamlit",
            type=ServiceType.BACKEND,
            port=8501,
            health_check_url="http://localhost:8501/health",
            startup_command="streamlit run app.py",
            timeout=10
        )
    }
    
    env_config = EnvironmentConfig(
        name="test",
        backend=BackendConfig(api_port=8000, streamlit_port=8501),
        frontend=FrontendConfig(port=3000),
        infrastructure=InfrastructureConfig(
            postgres={
                "host": "localhost",
                "port": 5432,
                "database": "test_db",
                "username": "test_user",
                "password": "test_pass"
            },
            redis={
                "host": "localhost",
                "port": 6379,
                "db": 0
            },
            minio={
                "endpoint": "localhost:9000",
                "access_key": "testkey",
                "secret_key": "testsecret",
                "secure": False
            }
        )
    )
    
    return SystemConfig(
        environment="test",
        services=services,
        environments={"test": env_config}
    )


class TestServiceHealthCheck:
    """Test HTTP service health checks."""
    
    @pytest.mark.asyncio
    async def test_healthy_service_check(self, sample_config):
        """Test health check for a healthy service."""
        service_config = sample_config.services["fastapi"]
        health_check = ServiceHealthCheck(service_config)
        
        # Mock successful HTTP response
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"status": "healthy"})
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await health_check.check_health()
            
            assert result.service_name == "fastapi"
            assert result.status == HealthStatus.HEALTHY
            assert result.response_time_ms > 0
            assert result.check_type == "http"
            assert result.details == {"status": "healthy"}
    
    @pytest.mark.asyncio
    async def test_unhealthy_service_check(self, sample_config):
        """Test health check for an unhealthy service."""
        service_config = sample_config.services["fastapi"]
        health_check = ServiceHealthCheck(service_config)
        
        # Mock failed HTTP response
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 503
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await health_check.check_health()
            
            assert result.service_name == "fastapi"
            assert result.status == HealthStatus.UNHEALTHY
            assert result.error_message == "HTTP 503"
    
    @pytest.mark.asyncio
    async def test_timeout_service_check(self, sample_config):
        """Test health check timeout handling."""
        service_config = sample_config.services["fastapi"]
        health_check = ServiceHealthCheck(service_config, timeout=1)
        
        # Mock timeout
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = asyncio.TimeoutError()
            
            result = await health_check.check_health()
            
            assert result.service_name == "fastapi"
            assert result.status == HealthStatus.UNHEALTHY
            assert "timeout" in result.error_message.lower()


class TestDatabaseHealthCheck:
    """Test database health checks."""
    
    @pytest.mark.asyncio
    async def test_healthy_database_check(self, sample_config):
        """Test health check for a healthy database."""
        db_config = sample_config.environments["test"].infrastructure.postgres
        health_check = DatabaseHealthCheck(db_config)
        
        # Mock successful database connection
        with patch('psycopg2.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_cursor.fetchone.side_effect = [
                (1,),  # SELECT 1 result
                (5, 100),  # active_connections, max_connections
                ("50 MB",)  # database size
            ]
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            
            result = await health_check.check_health()
            
            assert result.service_name == "postgresql"
            assert result.status == HealthStatus.HEALTHY
            assert result.check_type == "database"
            assert result.details["active_connections"] == 5
            assert result.details["max_connections"] == 100
    
    @pytest.mark.asyncio
    async def test_database_connection_error(self, sample_config):
        """Test database connection error handling."""
        db_config = sample_config.environments["test"].infrastructure.postgres
        health_check = DatabaseHealthCheck(db_config)
        
        # Mock connection error
        with patch('psycopg2.connect') as mock_connect:
            mock_connect.side_effect = Exception("Connection refused")
            
            result = await health_check.check_health()
            
            assert result.service_name == "postgresql"
            assert result.status == HealthStatus.UNHEALTHY
            assert "Connection refused" in result.error_message


class TestCacheHealthCheck:
    """Test Redis cache health checks."""
    
    @pytest.mark.asyncio
    async def test_healthy_cache_check(self, sample_config):
        """Test health check for a healthy Redis cache."""
        redis_config = sample_config.environments["test"].infrastructure.redis
        health_check = CacheHealthCheck(redis_config)
        
        # Mock successful Redis connection
        with patch('redis.Redis') as mock_redis:
            mock_instance = Mock()
            mock_instance.ping.return_value = True
            mock_instance.info.return_value = {
                'used_memory': 1024 * 1024,  # 1MB
                'maxmemory': 10 * 1024 * 1024,  # 10MB
                'connected_clients': 5,
                'keyspace_hits': 100,
                'keyspace_misses': 10
            }
            mock_redis.return_value = mock_instance
            
            result = await health_check.check_health()
            
            assert result.service_name == "redis"
            assert result.status == HealthStatus.HEALTHY
            assert result.check_type == "cache"
            assert result.details["memory_usage_mb"] == 1.0
            assert result.details["connected_clients"] == 5
    
    @pytest.mark.asyncio
    async def test_cache_connection_error(self, sample_config):
        """Test Redis connection error handling."""
        redis_config = sample_config.environments["test"].infrastructure.redis
        health_check = CacheHealthCheck(redis_config)
        
        # Mock connection error
        with patch('redis.Redis') as mock_redis:
            mock_instance = Mock()
            mock_instance.ping.side_effect = Exception("Connection refused")
            mock_redis.return_value = mock_instance
            
            result = await health_check.check_health()
            
            assert result.service_name == "redis"
            assert result.status == HealthStatus.UNHEALTHY
            assert "Connection refused" in result.error_message


class TestStorageHealthCheck:
    """Test MinIO storage health checks."""
    
    @pytest.mark.asyncio
    async def test_healthy_storage_check(self, sample_config):
        """Test health check for healthy MinIO storage."""
        minio_config = sample_config.environments["test"].infrastructure.minio
        health_check = StorageHealthCheck(minio_config)
        
        # Mock successful MinIO connection
        with patch('minio.Minio') as mock_minio:
            mock_instance = Mock()
            mock_bucket = Mock()
            mock_bucket.name = "test-bucket"
            mock_instance.list_buckets.return_value = [mock_bucket]
            mock_minio.return_value = mock_instance
            
            result = await health_check.check_health()
            
            assert result.service_name == "minio"
            assert result.status == HealthStatus.HEALTHY
            assert result.check_type == "storage"
            assert result.details["bucket_count"] == 1
    
    @pytest.mark.asyncio
    async def test_storage_connection_error(self, sample_config):
        """Test MinIO connection error handling."""
        minio_config = sample_config.environments["test"].infrastructure.minio
        health_check = StorageHealthCheck(minio_config)
        
        # Mock connection error
        with patch('minio.Minio') as mock_minio:
            mock_minio.side_effect = Exception("Connection refused")
            
            result = await health_check.check_health()
            
            assert result.service_name == "minio"
            assert result.status == HealthStatus.UNHEALTHY
            assert "Connection refused" in result.error_message


class TestFrontendHealthCheck:
    """Test frontend application health checks."""
    
    @pytest.mark.asyncio
    async def test_healthy_frontend_check(self):
        """Test health check for a healthy frontend."""
        frontend_config = {"port": 3000}
        health_check = FrontendHealthCheck(frontend_config)
        
        # Mock successful HTTP response with app content
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value="<div id='root'>React App</div>")
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await health_check.check_health()
            
            assert result.service_name == "frontend"
            assert result.status == HealthStatus.HEALTHY
            assert result.check_type == "frontend"
            assert result.details["is_app_content"] is True
    
    @pytest.mark.asyncio
    async def test_frontend_not_app_content(self):
        """Test frontend serving non-app content."""
        frontend_config = {"port": 3000}
        health_check = FrontendHealthCheck(frontend_config)
        
        # Mock HTTP response without app content
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value="<html><body>Not an app</body></html>")
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await health_check.check_health()
            
            assert result.service_name == "frontend"
            assert result.status == HealthStatus.DEGRADED
            assert result.details["is_app_content"] is False


class TestConnectivityHealthCheck:
    """Test service connectivity checks."""
    
    @pytest.mark.asyncio
    async def test_successful_connectivity_check(self):
        """Test successful connectivity between services."""
        connectivity_check = ConnectivityHealthCheck()
        
        # Mock successful socket connection
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_sock.connect_ex.return_value = 0  # Success
            mock_socket.return_value = mock_sock
            
            result = await connectivity_check.check_connectivity(
                "frontend", "backend", "http://localhost:8000/health"
            )
            
            assert result.service_name == "frontend->backend"
            assert result.status == HealthStatus.HEALTHY
            assert result.check_type == "connectivity"
            assert result.details["connection_result"] == "success"
    
    @pytest.mark.asyncio
    async def test_failed_connectivity_check(self):
        """Test failed connectivity between services."""
        connectivity_check = ConnectivityHealthCheck()
        
        # Mock failed socket connection
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_sock.connect_ex.return_value = 1  # Connection refused
            mock_socket.return_value = mock_sock
            
            result = await connectivity_check.check_connectivity(
                "frontend", "backend", "http://localhost:8000/health"
            )
            
            assert result.service_name == "frontend->backend"
            assert result.status == HealthStatus.UNHEALTHY
            assert "Connection failed: 1" in result.error_message


class TestHealthMonitor:
    """Test the main HealthMonitor class."""
    
    @pytest.mark.asyncio
    async def test_health_monitor_initialization(self, sample_config):
        """Test health monitor initialization."""
        health_monitor = HealthMonitor(sample_config)
        
        assert len(health_monitor.health_checks) == 2  # fastapi, streamlit
        assert len(health_monitor.database_checks) == 1  # postgresql
        assert len(health_monitor.cache_checks) == 1  # redis
        assert len(health_monitor.storage_checks) == 1  # minio
        assert len(health_monitor.frontend_checks) == 1  # frontend
    
    @pytest.mark.asyncio
    async def test_check_all_services(self, sample_config):
        """Test checking all services."""
        health_monitor = HealthMonitor(sample_config)
        
        # Mock all health checks to return healthy
        with patch.object(ServiceHealthCheck, 'check_health') as mock_service, \
             patch.object(DatabaseHealthCheck, 'check_health') as mock_db, \
             patch.object(CacheHealthCheck, 'check_health') as mock_cache, \
             patch.object(StorageHealthCheck, 'check_health') as mock_storage, \
             patch.object(FrontendHealthCheck, 'check_health') as mock_frontend:
            
            # Setup mock returns
            mock_service.return_value = HealthCheckResult(
                "test", HealthStatus.HEALTHY, 10.0, datetime.utcnow().isoformat()
            )
            mock_db.return_value = HealthCheckResult(
                "postgresql", HealthStatus.HEALTHY, 5.0, datetime.utcnow().isoformat()
            )
            mock_cache.return_value = HealthCheckResult(
                "redis", HealthStatus.HEALTHY, 3.0, datetime.utcnow().isoformat()
            )
            mock_storage.return_value = HealthCheckResult(
                "minio", HealthStatus.HEALTHY, 8.0, datetime.utcnow().isoformat()
            )
            mock_frontend.return_value = HealthCheckResult(
                "frontend", HealthStatus.HEALTHY, 15.0, datetime.utcnow().isoformat()
            )
            
            system_health = await health_monitor.check_all_services()
            
            assert system_health.overall_status == HealthStatus.HEALTHY
            assert system_health.healthy_services == system_health.total_services
            assert len(system_health.service_results) > 0
    
    @pytest.mark.asyncio
    async def test_check_specific_service(self, sample_config):
        """Test checking a specific service."""
        health_monitor = HealthMonitor(sample_config)
        
        # Mock service health check
        with patch.object(ServiceHealthCheck, 'check_health') as mock_check:
            mock_check.return_value = HealthCheckResult(
                "fastapi", HealthStatus.HEALTHY, 10.0, datetime.utcnow().isoformat()
            )
            
            result = await health_monitor.check_specific_service("fastapi")
            
            assert result is not None
            assert result.service_name == "fastapi"
            assert result.status == HealthStatus.HEALTHY
    
    @pytest.mark.asyncio
    async def test_connectivity_checks(self, sample_config):
        """Test service connectivity checks."""
        health_monitor = HealthMonitor(sample_config)
        
        # Mock connectivity check
        with patch.object(ConnectivityHealthCheck, 'check_connectivity') as mock_check:
            mock_check.return_value = HealthCheckResult(
                "frontend->backend", HealthStatus.HEALTHY, 5.0, 
                datetime.utcnow().isoformat(), check_type="connectivity"
            )
            
            results = await health_monitor.check_service_connectivity()
            
            assert len(results) > 0
            assert all(r.check_type == "connectivity" for r in results)
    
    @pytest.mark.asyncio
    async def test_detailed_health_report(self, sample_config):
        """Test getting detailed health report."""
        health_monitor = HealthMonitor(sample_config)
        
        # Mock all checks
        with patch.object(health_monitor, 'check_all_services') as mock_all, \
             patch.object(health_monitor, 'check_service_connectivity') as mock_conn:
            
            mock_all.return_value = Mock(
                overall_status=HealthStatus.HEALTHY,
                healthy_services=5,
                total_services=5,
                service_results=[
                    HealthCheckResult("test", HealthStatus.HEALTHY, 10.0, 
                                    datetime.utcnow().isoformat(), check_type="http")
                ]
            )
            mock_conn.return_value = [
                HealthCheckResult("test->test2", HealthStatus.HEALTHY, 5.0,
                                datetime.utcnow().isoformat(), check_type="connectivity")
            ]
            
            report = await health_monitor.get_detailed_health_report()
            
            assert report["overall_status"] == "healthy"
            assert "check_types" in report
            assert "summary" in report
    
    def test_get_health_check_endpoints(self, sample_config):
        """Test getting configured health check endpoints."""
        health_monitor = HealthMonitor(sample_config)
        endpoints = health_monitor.get_health_check_endpoints()
        
        assert "fastapi" in endpoints
        assert "streamlit" in endpoints
        assert "postgresql" in endpoints
        assert "redis" in endpoints
        assert "minio" in endpoints
        assert "frontend" in endpoints


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_health_endpoints_initialization(self, sample_config):
        """Test health endpoints initialization."""
        health_monitor = HealthMonitor(sample_config)
        health_endpoints = HealthEndpoints(health_monitor)
        
        assert health_endpoints.health_monitor == health_monitor
        assert health_endpoints.router is not None
        assert len(health_endpoints.router.routes) > 0
    
    @pytest.mark.asyncio
    async def test_streamlit_health_endpoints(self, sample_config):
        """Test Streamlit health endpoints."""
        health_monitor = HealthMonitor(sample_config)
        streamlit_endpoints = StreamlitHealthEndpoints(health_monitor)
        
        # Mock health monitor
        with patch.object(health_monitor, 'get_detailed_health_report') as mock_report:
            mock_report.return_value = {
                "overall_status": "healthy",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            health_data = await streamlit_endpoints.get_health_data()
            
            assert health_data["overall_status"] == "healthy"
            assert "timestamp" in health_data


def test_health_check_result_serialization():
    """Test HealthCheckResult serialization."""
    result = HealthCheckResult(
        service_name="test",
        status=HealthStatus.HEALTHY,
        response_time_ms=10.5,
        timestamp=datetime.utcnow().isoformat(),
        details={"key": "value"},
        check_type="http"
    )
    
    result_dict = result.to_dict()
    
    assert result_dict["service_name"] == "test"
    assert result_dict["status"] == "healthy"
    assert result_dict["response_time_ms"] == 10.5
    assert result_dict["details"] == {"key": "value"}
    assert result_dict["check_type"] == "http"


@pytest.mark.asyncio
async def test_health_monitoring_lifecycle(sample_config):
    """Test the complete health monitoring lifecycle."""
    health_monitor = HealthMonitor(sample_config, check_interval=1)
    
    # Start monitoring
    await health_monitor.start_monitoring()
    assert health_monitor.running is True
    
    # Let it run briefly
    await asyncio.sleep(2)
    
    # Check that history is being recorded
    history = health_monitor.get_health_history(hours=1)
    # Note: History might be empty in test due to mocked services
    
    # Stop monitoring
    await health_monitor.stop_monitoring()
    assert health_monitor.running is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])