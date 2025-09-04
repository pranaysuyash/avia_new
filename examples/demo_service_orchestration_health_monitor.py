#!/usr/bin/env python3
"""
Service Orchestration and Health Monitoring Demo

This demo showcases the integrated service orchestration and health monitoring system
that can actually start services and perform comprehensive health validation.
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path

# Add orchestration to path
import sys
sys.path.append('.')

from orchestration.config.models import (
    SystemConfig, ServiceConfig, ServiceType, EnvironmentConfig,
    BackendConfig, FrontendConfig, InfrastructureConfig
)
from orchestration.config.manager import ConfigurationManager
from orchestration.monitoring.service_orchestration_health_monitor import (
    ServiceOrchestrationHealthMonitor, ServiceStartupStatus
)


def create_demo_config() -> SystemConfig:
    """Create a comprehensive demo system configuration."""
    
    # Define services with realistic startup commands
    services = {
        "postgresql": ServiceConfig(
            name="postgresql",
            type=ServiceType.INFRASTRUCTURE,
            port=5432,
            health_check_url="postgresql://localhost:5432",
            startup_command="pg_ctl start -D /usr/local/var/postgres",
            timeout=15,
            dependencies=[]
        ),
        "redis": ServiceConfig(
            name="redis",
            type=ServiceType.INFRASTRUCTURE,
            port=6379,
            health_check_url="redis://localhost:6379",
            startup_command="redis-server",
            timeout=10,
            dependencies=[]
        ),
        "minio": ServiceConfig(
            name="minio",
            type=ServiceType.INFRASTRUCTURE,
            port=9000,
            health_check_url="http://localhost:9000/minio/health/ready",
            startup_command="minio server /tmp/minio-data --console-address :9001",
            timeout=15,
            dependencies=[]
        ),
        "fastapi": ServiceConfig(
            name="fastapi",
            type=ServiceType.BACKEND,
            port=8000,
            health_check_url="http://localhost:8000/health",
            startup_command="uvicorn api.main:app --host 0.0.0.0 --port 8000",
            timeout=20,
            dependencies=["postgresql", "redis", "minio"]
        ),
        "streamlit": ServiceConfig(
            name="streamlit",
            type=ServiceType.BACKEND,
            port=8501,
            health_check_url="http://localhost:8501/health",
            startup_command="streamlit run app.py --server.port 8501",
            timeout=25,
            dependencies=["fastapi"]
        ),
        "frontend": ServiceConfig(
            name="frontend",
            type=ServiceType.FRONTEND,
            port=3000,
            health_check_url="http://localhost:3000",
            startup_command="npm start",
            timeout=30,
            dependencies=["fastapi"]
        )
    }
    
    # Define environment configuration
    env_config = EnvironmentConfig(
        name="development",
        backend=BackendConfig(
            api_port=8000,
            streamlit_port=8501,
            debug=True
        ),
        frontend=FrontendConfig(
            port=3000,
            api_url="http://localhost:8000"
        ),
        infrastructure=InfrastructureConfig(
            postgres={
                "host": "localhost",
                "port": 5432,
                "database": "transcription_dev",
                "username": "postgres",
                "password": "postgres"
            },
            redis={
                "host": "localhost",
                "port": 6379,
                "db": 0
            },
            minio={
                "endpoint": "localhost:9000",
                "access_key": "minioadmin",
                "secret_key": "minioadmin",
                "secure": False
            }
        )
    )
    
    return SystemConfig(
        environment="development",
        services=services,
        environments={"development": env_config}
    )


async def demo_system_initialization():
    """Demonstrate system initialization."""
    print("🚀 Service Orchestration and Health Monitoring Demo")
    print("=" * 55)
    
    # Create configuration manager
    config_manager = ConfigurationManager()
    
    # Create demo configuration
    demo_config = create_demo_config()
    
    # Save configuration temporarily
    config_path = Path("orchestration/configs/demo.yaml")
    success = config_manager.save_configuration(demo_config, str(config_path))
    
    if not success:
        print("❌ Failed to save demo configuration")
        return None
    
    # Load configuration through manager
    config_manager.config_file = str(config_path)
    
    # Create orchestration health monitor
    orchestration_monitor = ServiceOrchestrationHealthMonitor(config_manager)
    
    print("🔧 Initializing orchestration and health monitoring system...")
    success = await orchestration_monitor.initialize()
    
    if success:
        print("✅ System initialized successfully")
        print(f"   Services configured: {len(orchestration_monitor.system_config.services)}")
        print(f"   Startup order: {' -> '.join(orchestration_monitor.startup_order)}")
        print()
        return orchestration_monitor
    else:
        print("❌ System initialization failed")
        return None


async def demo_system_readiness_validation(orchestration_monitor):
    """Demonstrate system readiness validation."""
    print("🔍 System Readiness Validation")
    print("=" * 30)
    
    validation_result = await orchestration_monitor.validate_system_readiness()
    
    print(f"Overall Ready: {'✅ YES' if validation_result['ready'] else '❌ NO'}")
    print()
    
    # Show detailed checks
    for check_name, check_result in validation_result['checks'].items():
        print(f"📋 {check_name.title()} Check:")
        
        if check_name == 'configuration':
            status = "✅ VALID" if check_result['valid'] else "❌ INVALID"
            print(f"   Status: {status}")
            if check_result.get('errors'):
                for error in check_result['errors']:
                    print(f"   Error: {error}")
        
        elif check_name == 'services':
            all_ready = check_result['all_services_started']
            status = "✅ ALL READY" if all_ready else "⚠️ SOME NOT READY"
            print(f"   Status: {status}")
            
            for service_name, service_status in check_result['service_status'].items():
                service_icon = "✅" if service_status['ready'] else "❌"
                print(f"   {service_icon} {service_name}: {service_status['status']}")
        
        elif check_name == 'health_monitoring':
            if 'error' in check_result:
                print(f"   ❌ Error: {check_result['error']}")
            else:
                monitor_status = "✅ RUNNING" if check_result['monitor_running'] else "❌ STOPPED"
                print(f"   Monitor: {monitor_status}")
                print(f"   Checks configured: {check_result['checks_configured']}")
                print(f"   Recent health data: {'✅ Available' if check_result['recent_health_available'] else '❌ None'}")
        
        print()


async def demo_comprehensive_service_startup(orchestration_monitor):
    """Demonstrate comprehensive service startup with health monitoring."""
    print("🚀 Comprehensive Service Startup with Health Monitoring")
    print("=" * 55)
    
    print("Starting all services with dependency resolution and health validation...")
    print("Note: Some services may fail if not actually installed/configured")
    print()
    
    # Start all services
    startup_result = await orchestration_monitor.start_all_services_with_health_monitoring()
    
    # Display results
    print(f"🎯 Startup Results:")
    print(f"   Overall Status: {startup_result.overall_status.value.upper()}")
    print(f"   Total Time: {startup_result.startup_time_ms:.2f}ms")
    print(f"   Success Rate: {startup_result.successful_services}/{startup_result.total_services}")
    print()
    
    # Show individual service results
    print("📊 Individual Service Results:")
    for result in startup_result.service_results:
        status_icon = "✅" if result.status == ServiceStartupStatus.HEALTHY else "⚠️" if result.status == ServiceStartupStatus.STARTED else "❌"
        print(f"   {status_icon} {result.service_name}:")
        print(f"      Status: {result.status.value}")
        print(f"      Startup Time: {result.startup_time_ms:.2f}ms")
        
        if result.dependencies_started:
            print(f"      Dependencies Started: {', '.join(result.dependencies_started)}")
        
        if result.health_check_result:
            health_status = result.health_check_result.status.value
            response_time = result.health_check_result.response_time_ms
            print(f"      Health Check: {health_status} ({response_time:.1f}ms)")
        
        if result.error_message:
            print(f"      Error: {result.error_message}")
        
        print()
    
    # Show system health if available
    if startup_result.system_health:
        print("🏥 System Health Summary:")
        health = startup_result.system_health
        print(f"   Overall: {health.overall_status.value}")
        print(f"   Healthy Services: {health.healthy_services}/{health.total_services}")
        print(f"   Timestamp: {health.timestamp}")
        print()
    
    return startup_result


async def demo_current_system_status(orchestration_monitor):
    """Demonstrate getting current system status."""
    print("📊 Current System Status")
    print("=" * 25)
    
    status = await orchestration_monitor.get_current_system_status()
    
    print(f"System Started: {'✅ YES' if status['system_started'] else '❌ NO'}")
    print(f"Startup In Progress: {'⏳ YES' if status['startup_in_progress'] else '✅ NO'}")
    print(f"Timestamp: {status['timestamp']}")
    print()
    
    # Show service status
    print("🔧 Service Status:")
    for service_name, service_info in status['services'].items():
        startup_status = service_info['startup_status']
        startup_time = service_info.get('startup_time_ms', 0)
        
        status_icon = "✅" if startup_status == 'healthy' else "⚠️" if startup_status == 'started' else "❌"
        print(f"   {status_icon} {service_name}: {startup_status}")
        
        if startup_time > 0:
            print(f"      Startup Time: {startup_time:.2f}ms")
        
        if 'current_health' in service_info:
            health = service_info['current_health']
            print(f"      Current Health: {health['status']} ({health['response_time_ms']:.1f}ms)")
        
        if 'health_check_error' in service_info:
            print(f"      Health Check Error: {service_info['health_check_error']}")
    
    print()
    
    # Show system health if available
    if 'system_health' in status:
        health = status['system_health']
        print("🏥 Current System Health:")
        print(f"   Overall Status: {health['overall_status']}")
        print(f"   Healthy Services: {health['healthy_services']}/{health['total_services']}")
        print()
    
    # Show health monitor status
    if 'health_monitor' in status:
        monitor = status['health_monitor']
        print("🔍 Health Monitor Status:")
        print(f"   Running: {'✅ YES' if monitor['running'] else '❌ NO'}")
        print(f"   Check Interval: {monitor['check_interval']}s")
        print(f"   Total Checks: {monitor['total_checks_configured']}")
        print(f"   History Size: {monitor['history_size']}/{monitor['max_history_size']}")
        
        breakdown = monitor['checker_breakdown']
        print(f"   Checker Breakdown:")
        print(f"      HTTP Services: {breakdown['http_services']}")
        print(f"      Databases: {breakdown['databases']}")
        print(f"      Caches: {breakdown['caches']}")
        print(f"      Storage: {breakdown['storage']}")
        print(f"      Frontends: {breakdown['frontends']}")
    
    print()


async def demo_service_restart_with_health_check(orchestration_monitor):
    """Demonstrate service restart with health verification."""
    print("🔄 Service Restart with Health Check")
    print("=" * 35)
    
    # Try to restart a service (use one that's likely to be available)
    service_to_restart = "streamlit"  # Usually available in our setup
    
    print(f"Restarting service: {service_to_restart}")
    
    try:
        restart_result = await orchestration_monitor.restart_service_with_health_check(service_to_restart)
        
        status_icon = "✅" if restart_result.status == ServiceStartupStatus.HEALTHY else "⚠️" if restart_result.status == ServiceStartupStatus.STARTED else "❌"
        print(f"{status_icon} Restart Result:")
        print(f"   Service: {restart_result.service_name}")
        print(f"   Status: {restart_result.status.value}")
        print(f"   Restart Time: {restart_result.startup_time_ms:.2f}ms")
        
        if restart_result.health_check_result:
            health = restart_result.health_check_result
            print(f"   Health Check: {health.status.value} ({health.response_time_ms:.1f}ms)")
        
        if restart_result.error_message:
            print(f"   Error: {restart_result.error_message}")
        
    except Exception as e:
        print(f"❌ Restart failed: {e}")
    
    print()


async def demo_system_shutdown(orchestration_monitor):
    """Demonstrate system shutdown."""
    print("🛑 System Shutdown")
    print("=" * 18)
    
    print("Stopping all services and health monitoring...")
    
    try:
        stop_results = await orchestration_monitor.stop_all_services()
        
        print("📊 Shutdown Results:")
        for service_name, success in stop_results.items():
            status_icon = "✅" if success else "❌"
            print(f"   {status_icon} {service_name}: {'Stopped' if success else 'Failed to stop'}")
        
        print()
        print("✅ System shutdown completed")
        
    except Exception as e:
        print(f"❌ Shutdown failed: {e}")


def save_demo_results(startup_result, final_status):
    """Save demo results to file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"service_orchestration_demo_results_{timestamp}.json"
    
    try:
        results = {
            "timestamp": datetime.now().isoformat(),
            "startup_result": startup_result.to_dict() if startup_result else None,
            "final_status": final_status
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"💾 Demo results saved to: {filename}")
        
    except Exception as e:
        print(f"❌ Error saving demo results: {e}")


async def main():
    """Run the complete service orchestration and health monitoring demo."""
    orchestration_monitor = None
    startup_result = None
    
    try:
        # Initialize system
        orchestration_monitor = await demo_system_initialization()
        if not orchestration_monitor:
            return
        
        # Validate system readiness
        await demo_system_readiness_validation(orchestration_monitor)
        
        # Start all services with health monitoring
        startup_result = await demo_comprehensive_service_startup(orchestration_monitor)
        
        # Show current system status
        await demo_current_system_status(orchestration_monitor)
        
        # Demonstrate service restart
        await demo_service_restart_with_health_check(orchestration_monitor)
        
        # Get final status
        final_status = await orchestration_monitor.get_current_system_status()
        
        # Save results
        save_demo_results(startup_result, final_status)
        
        print("🎉 Service orchestration and health monitoring demo completed!")
        
        # Shutdown system
        await demo_system_shutdown(orchestration_monitor)
        
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
        if orchestration_monitor:
            await orchestration_monitor.stop_all_services()
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        if orchestration_monitor:
            try:
                await orchestration_monitor.stop_all_services()
            except:
                pass


if __name__ == "__main__":
    asyncio.run(main())