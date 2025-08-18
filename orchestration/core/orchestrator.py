"""Main service orchestrator for managing all services."""

import asyncio
import time
from typing import Dict, List, Optional, Set
from collections import defaultdict, deque
import logging

from ..config.models import SystemConfig, ServiceConfig
from ..config.manager import ConfigurationManager
from .service_manager import ServiceManager, BackendServiceManager, InfrastructureServiceManager
from .frontend_manager import FrontendServiceFactory
from .types import ServiceInfo, ServiceStatus, ServiceType, SystemHealth, StartupResult

logger = logging.getLogger(__name__)


class ServiceOrchestrator:
    """Orchestrates all services in the system."""
    
    def __init__(self, config_manager: ConfigurationManager):
        self.config_manager = config_manager
        self.system_config: Optional[SystemConfig] = None
        self.service_managers: Dict[str, ServiceManager] = {}
        self.startup_order: List[str] = []
        self.running = False
        self.monitor_task: Optional[asyncio.Task] = None
        
    async def initialize(self) -> bool:
        """Initialize the orchestrator with system configuration."""
        try:
            # Load system configuration
            self.system_config = self.config_manager.load_system_config()
            
            # Validate configuration
            validation_result = self.config_manager.validate_configuration(self.system_config)
            if not validation_result.is_valid:
                logger.error(f"Invalid system configuration: {validation_result.errors}")
                return False
            
            # Create service managers
            self._create_service_managers()
            
            # Calculate startup order based on dependencies
            self.startup_order = self._calculate_startup_order()
            
            logger.info(f"Orchestrator initialized with {len(self.service_managers)} services")
            logger.info(f"Startup order: {' -> '.join(self.startup_order)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            return False
    
    def _create_service_managers(self):
        """Create appropriate service managers for each service."""
        for service_name, service_config in self.system_config.services.items():
            if service_config.type == ServiceType.BACKEND:
                manager = BackendServiceManager(service_config)
            elif service_config.type == ServiceType.INFRASTRUCTURE:
                manager = InfrastructureServiceManager(service_config)
            elif service_config.type in [ServiceType.FRONTEND, ServiceType.MOBILE, ServiceType.DESKTOP]:
                manager = FrontendServiceFactory.create_manager(service_config)
            else:
                manager = ServiceManager(service_config)
            
            self.service_managers[service_name] = manager
            logger.debug(f"Created {type(manager).__name__} for service: {service_name}")
    
    def _calculate_startup_order(self) -> List[str]:
        """Calculate service startup order based on dependencies."""
        # Build dependency graph
        dependencies = {}
        for service_name, service_config in self.system_config.services.items():
            dependencies[service_name] = set(service_config.dependencies)
        
        # Topological sort to determine startup order
        order = []
        visited = set()
        temp_visited = set()
        
        def visit(service_name: str):
            if service_name in temp_visited:
                raise ValueError(f"Circular dependency detected involving service: {service_name}")
            if service_name in visited:
                return
            
            temp_visited.add(service_name)
            
            # Visit dependencies first
            for dependency in dependencies.get(service_name, set()):
                if dependency in dependencies:  # Only if dependency is a managed service
                    visit(dependency)
            
            temp_visited.remove(service_name)
            visited.add(service_name)
            order.append(service_name)
        
        # Visit all services
        for service_name in dependencies:
            if service_name not in visited:
                visit(service_name)
        
        return order
    
    async def start_all_services(self) -> Dict[str, StartupResult]:
        """Start all services in dependency order."""
        if not self.system_config:
            raise RuntimeError("Orchestrator not initialized")
        
        logger.info("Starting all services...")
        results = {}
        
        for service_name in self.startup_order:
            if service_name in self.service_managers:
                logger.info(f"Starting service: {service_name}")
                result = await self.service_managers[service_name].start()
                results[service_name] = result
                
                if not result.success:
                    logger.error(f"Failed to start service {service_name}: {result.error_message}")
                    # Continue with other services even if one fails
                else:
                    logger.info(f"Service {service_name} started successfully")
                    
                # Wait a moment between service starts
                await asyncio.sleep(2)
        
        # Start monitoring
        if not self.running:
            await self.start_monitoring()
        
        return results
    
    async def stop_all_services(self) -> Dict[str, bool]:
        """Stop all services in reverse dependency order."""
        if not self.system_config:
            return {}
        
        logger.info("Stopping all services...")
        
        # Stop monitoring first
        await self.stop_monitoring()
        
        results = {}
        
        # Stop services in reverse order
        for service_name in reversed(self.startup_order):
            if service_name in self.service_managers:
                logger.info(f"Stopping service: {service_name}")
                result = await self.service_managers[service_name].stop()
                results[service_name] = result
                
                if not result:
                    logger.error(f"Failed to stop service: {service_name}")
                else:
                    logger.info(f"Service {service_name} stopped successfully")
                    
                # Wait a moment between service stops
                await asyncio.sleep(1)
        
        return results
    
    async def start_service(self, service_name: str) -> StartupResult:
        """Start a specific service."""
        if service_name not in self.service_managers:
            return StartupResult(
                success=False,
                error_message=f"Service {service_name} not found"
            )
        
        # Check dependencies
        service_config = self.system_config.services[service_name]
        for dependency in service_config.dependencies:
            if dependency in self.service_managers:
                dep_manager = self.service_managers[dependency]
                if not dep_manager.is_running():
                    logger.warning(f"Dependency {dependency} is not running, starting it first")
                    dep_result = await self.start_service(dependency)
                    if not dep_result.success:
                        return StartupResult(
                            success=False,
                            error_message=f"Failed to start dependency {dependency}: {dep_result.error_message}"
                        )
        
        return await self.service_managers[service_name].start()
    
    async def stop_service(self, service_name: str) -> bool:
        """Stop a specific service."""
        if service_name not in self.service_managers:
            logger.error(f"Service {service_name} not found")
            return False
        
        # Check if other services depend on this one
        dependents = []
        for name, config in self.system_config.services.items():
            if service_name in config.dependencies and name in self.service_managers:
                if self.service_managers[name].is_running():
                    dependents.append(name)
        
        if dependents:
            logger.warning(f"Service {service_name} has running dependents: {dependents}")
            # Stop dependents first
            for dependent in dependents:
                await self.stop_service(dependent)
        
        return await self.service_managers[service_name].stop()
    
    async def restart_service(self, service_name: str) -> StartupResult:
        """Restart a specific service."""
        if service_name not in self.service_managers:
            return StartupResult(
                success=False,
                error_message=f"Service {service_name} not found"
            )
        
        return await self.service_managers[service_name].restart()
    
    def get_service_status(self, service_name: str) -> Optional[ServiceInfo]:
        """Get status of a specific service."""
        if service_name not in self.service_managers:
            return None
        
        return self.service_managers[service_name].get_status()
    
    def get_all_services_status(self) -> Dict[str, ServiceInfo]:
        """Get status of all services."""
        status = {}
        for service_name, manager in self.service_managers.items():
            status[service_name] = manager.get_status()
        return status
    
    def get_system_health(self) -> SystemHealth:
        """Get overall system health."""
        if not self.service_managers:
            return SystemHealth.UNKNOWN
        
        running_count = 0
        total_count = len(self.service_managers)
        failed_count = 0
        
        for manager in self.service_managers.values():
            status = manager.get_status()
            if status.status == ServiceStatus.RUNNING:
                running_count += 1
            elif status.status == ServiceStatus.FAILED:
                failed_count += 1
        
        if running_count == total_count:
            return SystemHealth.HEALTHY
        elif running_count > 0:
            return SystemHealth.DEGRADED
        else:
            return SystemHealth.UNHEALTHY
    
    async def start_monitoring(self):
        """Start service monitoring."""
        if self.running:
            return
        
        self.running = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Started service monitoring")
    
    async def stop_monitoring(self):
        """Stop service monitoring."""
        if not self.running:
            return
        
        self.running = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
            self.monitor_task = None
        
        logger.info("Stopped service monitoring")
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                # Check health of all services
                for service_name, manager in self.service_managers.items():
                    try:
                        is_healthy = await manager.health_check()
                        if not is_healthy:
                            logger.warning(f"Service {service_name} health check failed")
                            
                            # Check if service needs restart
                            status = manager.get_status()
                            if status.status == ServiceStatus.STOPPED and manager.restart_attempts < manager.max_restart_attempts:
                                logger.info(f"Attempting to restart failed service: {service_name}")
                                await manager.restart()
                    
                    except Exception as e:
                        logger.error(f"Error during health check for {service_name}: {e}")
                
                # Wait before next check
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(30)
    
    def get_service_dependencies(self, service_name: str) -> List[str]:
        """Get dependencies for a service."""
        if service_name not in self.system_config.services:
            return []
        
        return list(self.system_config.services[service_name].dependencies)
    
    def get_service_dependents(self, service_name: str) -> List[str]:
        """Get services that depend on the given service."""
        dependents = []
        for name, config in self.system_config.services.items():
            if service_name in config.dependencies:
                dependents.append(name)
        return dependents
    
    async def reload_configuration(self) -> bool:
        """Reload system configuration."""
        try:
            # Stop all services
            await self.stop_all_services()
            
            # Reload configuration
            self.system_config = self.config_manager.load_system_config()
            
            # Validate new configuration
            validation_result = self.config_manager.validate_configuration(self.system_config)
            if not validation_result.is_valid:
                logger.error(f"Invalid reloaded configuration: {validation_result.errors}")
                return False
            
            # Recreate service managers
            self.service_managers.clear()
            self._create_service_managers()
            
            # Recalculate startup order
            self.startup_order = self._calculate_startup_order()
            
            logger.info("Configuration reloaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            return False
    
    def get_orchestrator_stats(self) -> Dict[str, any]:
        """Get orchestrator statistics."""
        service_stats = {}
        for service_name, manager in self.service_managers.items():
            status = manager.get_status()
            resource_usage = manager.get_resource_usage()
            
            service_stats[service_name] = {
                'status': status.to_dict(),
                'resource_usage': resource_usage
            }
        
        return {
            'total_services': len(self.service_managers),
            'running_services': sum(1 for m in self.service_managers.values() if m.is_running()),
            'system_health': self.get_system_health().value,
            'startup_order': self.startup_order,
            'monitoring_active': self.running,
            'services': service_stats
        }