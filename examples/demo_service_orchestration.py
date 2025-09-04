#!/usr/bin/env python3
"""
Demo script for Service Orchestration Engine

This script demonstrates the service orchestration capabilities including:
- Service lifecycle management
- Dependency resolution and startup ordering
- Health monitoring and automatic restart
- Configuration management integration
"""

import asyncio
import logging
import time
from pathlib import Path

from orchestration.config.manager import ConfigurationManager
from orchestration.core.orchestrator import ServiceOrchestrator
from orchestration.core.types import ServiceStatus, SystemHealth

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_basic_orchestration():
    """Demonstrate basic service orchestration."""
    print("\n" + "="*60)
    print("DEMO: Basic Service Orchestration")
    print("="*60)
    
    # Initialize configuration manager
    config_manager = ConfigurationManager("orchestration/configs")
    
    # Initialize orchestrator
    orchestrator = ServiceOrchestrator(config_manager)
    
    print("\n1. Initializing orchestrator...")
    success = await orchestrator.initialize()
    
    if success:
        print("   ✅ Orchestrator initialized successfully")
        print(f"   Services: {list(orchestrator.service_managers.keys())}")
        print(f"   Startup order: {' -> '.join(orchestrator.startup_order)}")
    else:
        print("   ❌ Failed to initialize orchestrator")
        return None
    
    return orchestrator


async def demo_service_lifecycle(orchestrator):
    """Demonstrate service lifecycle management."""
    print("\n" + "="*60)
    print("DEMO: Service Lifecycle Management")
    print("="*60)
    
    # Get initial status
    print("\n1. Initial service status:")
    status = orchestrator.get_all_services_status()
    for service_name, service_info in status.items():
        print(f"   {service_name}: {service_info.status.value}")
    
    # Start a specific service (infrastructure first)
    print("\n2. Starting infrastructure services...")
    infra_services = [name for name, manager in orchestrator.service_managers.items() 
                     if manager.config.type.value == "infrastructure"]
    
    for service_name in infra_services[:2]:  # Start first 2 infrastructure services
        print(f"   Starting {service_name}...")
        result = await orchestrator.start_service(service_name)
        if result.success:
            print(f"   ✅ {service_name} started successfully")
        else:
            print(f"   ❌ Failed to start {service_name}: {result.error_message}")
        
        # Wait a moment
        await asyncio.sleep(2)
    
    # Check status after starting some services
    print("\n3. Service status after starting infrastructure:")
    status = orchestrator.get_all_services_status()
    for service_name, service_info in status.items():
        print(f"   {service_name}: {service_info.status.value}")
    
    # Stop services
    print("\n4. Stopping started services...")
    for service_name in infra_services[:2]:
        print(f"   Stopping {service_name}...")
        success = await orchestrator.stop_service(service_name)
        if success:
            print(f"   ✅ {service_name} stopped successfully")
        else:
            print(f"   ❌ Failed to stop {service_name}")


async def demo_dependency_resolution(orchestrator):
    """Demonstrate dependency resolution."""
    print("\n" + "="*60)
    print("DEMO: Dependency Resolution")
    print("="*60)
    
    # Show service dependencies
    print("\n1. Service dependencies:")
    for service_name in orchestrator.service_managers.keys():
        dependencies = orchestrator.get_service_dependencies(service_name)
        dependents = orchestrator.get_service_dependents(service_name)
        
        print(f"   {service_name}:")
        print(f"     Dependencies: {dependencies if dependencies else 'None'}")
        print(f"     Dependents: {dependents if dependents else 'None'}")
    
    # Demonstrate startup order calculation
    print(f"\n2. Calculated startup order: {' -> '.join(orchestrator.startup_order)}")
    
    # Try starting a service with dependencies
    backend_services = [name for name, manager in orchestrator.service_managers.items() 
                       if manager.config.type.value == "backend"]
    
    if backend_services:
        service_name = backend_services[0]
        dependencies = orchestrator.get_service_dependencies(service_name)
        
        print(f"\n3. Starting {service_name} (which depends on: {dependencies})...")
        result = await orchestrator.start_service(service_name)
        
        if result.success:
            print(f"   ✅ {service_name} and its dependencies started successfully")
        else:
            print(f"   ❌ Failed to start {service_name}: {result.error_message}")
        
        # Check what actually started
        print("\n4. Services that are now running:")
        status = orchestrator.get_all_services_status()
        for name, info in status.items():
            if info.status == ServiceStatus.RUNNING:
                print(f"   ✅ {name}: {info.status.value}")
        
        # Clean up
        print(f"\n5. Stopping {service_name}...")
        await orchestrator.stop_service(service_name)


async def demo_health_monitoring(orchestrator):
    """Demonstrate health monitoring."""
    print("\n" + "="*60)
    print("DEMO: Health Monitoring")
    print("="*60)
    
    # Start monitoring
    print("\n1. Starting health monitoring...")
    await orchestrator.start_monitoring()
    print("   ✅ Health monitoring started")
    
    # Get system health
    print("\n2. Current system health:")
    system_health = orchestrator.get_system_health()
    print(f"   System Health: {system_health.value}")
    
    # Show orchestrator stats
    print("\n3. Orchestrator statistics:")
    stats = orchestrator.get_orchestrator_stats()
    print(f"   Total services: {stats['total_services']}")
    print(f"   Running services: {stats['running_services']}")
    print(f"   System health: {stats['system_health']}")
    print(f"   Monitoring active: {stats['monitoring_active']}")
    
    # Monitor for a short time
    print("\n4. Monitoring services for 10 seconds...")
    await asyncio.sleep(10)
    
    # Stop monitoring
    print("\n5. Stopping health monitoring...")
    await orchestrator.stop_monitoring()
    print("   ✅ Health monitoring stopped")


async def demo_configuration_integration(orchestrator):
    """Demonstrate configuration integration."""
    print("\n" + "="*60)
    print("DEMO: Configuration Integration")
    print("="*60)
    
    # Show current configuration
    print("\n1. Current system configuration:")
    if orchestrator.system_config:
        print(f"   Environment: {orchestrator.system_config.environment}")
        print(f"   Services configured: {len(orchestrator.system_config.services)}")
        print(f"   Environments available: {list(orchestrator.system_config.environments.keys())}")
    
    # Show service configurations
    print("\n2. Service configurations:")
    for service_name, manager in orchestrator.service_managers.items():
        config = manager.config
        print(f"   {service_name}:")
        print(f"     Type: {config.type.value}")
        print(f"     Port: {config.port}")
        print(f"     Command: {config.startup_command}")
        print(f"     Dependencies: {config.dependencies}")
    
    # Demonstrate configuration reload (simulation)
    print("\n3. Configuration reload capability:")
    print("   Configuration can be reloaded without stopping the orchestrator")
    print("   This allows for dynamic service management updates")


async def demo_error_handling():
    """Demonstrate error handling scenarios."""
    print("\n" + "="*60)
    print("DEMO: Error Handling")
    print("="*60)
    
    # Test with invalid configuration
    print("\n1. Testing with invalid configuration path...")
    config_manager = ConfigurationManager("nonexistent/path")
    orchestrator = ServiceOrchestrator(config_manager)
    
    try:
        success = await orchestrator.initialize()
        if not success:
            print("   ✅ Properly handled invalid configuration")
    except Exception as e:
        print(f"   ✅ Caught configuration error: {e}")
    
    # Test starting non-existent service
    print("\n2. Testing start of non-existent service...")
    config_manager = ConfigurationManager("orchestration/configs")
    orchestrator = ServiceOrchestrator(config_manager)
    await orchestrator.initialize()
    
    result = await orchestrator.start_service("nonexistent-service")
    if not result.success:
        print(f"   ✅ Properly handled non-existent service: {result.error_message}")


async def demo_advanced_features(orchestrator):
    """Demonstrate advanced orchestration features."""
    print("\n" + "="*60)
    print("DEMO: Advanced Features")
    print("="*60)
    
    # Demonstrate service restart
    print("\n1. Service restart capability:")
    backend_services = [name for name, manager in orchestrator.service_managers.items() 
                       if manager.config.type.value == "backend"]
    
    if backend_services:
        service_name = backend_services[0]
        print(f"   Restarting {service_name}...")
        result = await orchestrator.restart_service(service_name)
        if result.success:
            print(f"   ✅ {service_name} restarted successfully")
        else:
            print(f"   ❌ Failed to restart {service_name}: {result.error_message}")
    
    # Demonstrate resource monitoring
    print("\n2. Resource usage monitoring:")
    for service_name, manager in orchestrator.service_managers.items():
        if manager.is_running():
            usage = manager.get_resource_usage()
            if usage:
                print(f"   {service_name}:")
                print(f"     CPU: {usage.get('cpu_percent', 0):.1f}%")
                print(f"     Memory: {usage.get('memory_percent', 0):.1f}%")
    
    # Show startup order optimization
    print("\n3. Startup order optimization:")
    print("   The orchestrator automatically calculates optimal startup order")
    print("   based on service dependencies to minimize startup time")
    print(f"   Current order: {' -> '.join(orchestrator.startup_order)}")


async def main():
    """Main demo function."""
    print("🚀 Service Orchestration Engine Demo")
    print("This demo showcases the service orchestration capabilities")
    
    try:
        # Basic orchestration demo
        orchestrator = await demo_basic_orchestration()
        
        if orchestrator:
            # Service lifecycle demo
            await demo_service_lifecycle(orchestrator)
            
            # Dependency resolution demo
            await demo_dependency_resolution(orchestrator)
            
            # Health monitoring demo
            await demo_health_monitoring(orchestrator)
            
            # Configuration integration demo
            await demo_configuration_integration(orchestrator)
            
            # Advanced features demo
            await demo_advanced_features(orchestrator)
            
            # Clean up
            print("\n" + "="*60)
            print("CLEANUP: Stopping all services")
            print("="*60)
            await orchestrator.stop_all_services()
        
        # Error handling demo
        await demo_error_handling()
        
        print("\n" + "="*60)
        print("✅ Service Orchestration Engine Demo Complete!")
        print("="*60)
        print("\nKey Features Demonstrated:")
        print("• Service lifecycle management (start, stop, restart)")
        print("• Dependency resolution and startup ordering")
        print("• Health monitoring with automatic recovery")
        print("• Configuration integration and validation")
        print("• Resource usage monitoring")
        print("• Error handling and graceful degradation")
        print("• Multi-service type support (backend, frontend, infrastructure)")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)