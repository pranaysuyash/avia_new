#!/usr/bin/env python3
"""
Simple Health Monitoring System Demo

This demo showcases the core health monitoring capabilities with graceful
handling of missing dependencies and services.
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
from orchestration.monitoring.health import HealthMonitor, HealthStatus


def create_demo_config() -> SystemConfig:
    """Create a demo system configuration."""
    
    # Define services
    services = {
        "fastapi": ServiceConfig(
            name="fastapi",
            type=ServiceType.BACKEND,
            port=8000,
            health_check_url="http://localhost:8000/health",
            startup_command="uvicorn api.main:app --host 0.0.0.0 --port 8000",
            timeout=5
        ),
        "streamlit": ServiceConfig(
            name="streamlit",
            type=ServiceType.BACKEND,
            port=8501,
            health_check_url="http://localhost:8501/health",
            startup_command="streamlit run app.py --server.port 8501",
            timeout=5
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
                "database": "postgres",  # Use default postgres db
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


async def demo_basic_health_checks():
    """Demonstrate basic health check functionality."""
    print("🏥 Health Monitoring System Demo")
    print("=" * 40)
    
    # Create configuration and health monitor
    config = create_demo_config()
    health_monitor = HealthMonitor(config, check_interval=30)
    
    print(f"✅ Initialized health monitor")
    print(f"   • HTTP services: {len(health_monitor.health_checks)}")
    print(f"   • Database checks: {len(health_monitor.database_checks)}")
    print(f"   • Cache checks: {len(health_monitor.cache_checks)}")
    print(f"   • Storage checks: {len(health_monitor.storage_checks)}")
    print(f"   • Frontend checks: {len(health_monitor.frontend_checks)}")
    print()
    
    # Perform health check
    print("🔍 Running health checks...")
    start_time = time.time()
    
    try:
        system_health = await health_monitor.check_all_services()
        check_time = time.time() - start_time
        
        print(f"⏱️  Completed in {check_time:.2f} seconds")
        print()
        
        # Display overall status
        status_icon = "✅" if system_health.overall_status == HealthStatus.HEALTHY else "⚠️" if system_health.overall_status.name == "DEGRADED" else "❌"
        print(f"📊 System Status: {status_icon} {system_health.overall_status.value.upper()}")
        print(f"   Healthy: {system_health.healthy_services}/{system_health.total_services} services")
        print()
        
        # Group results by type
        results_by_type = {}
        for result in system_health.service_results:
            check_type = result.check_type
            if check_type not in results_by_type:
                results_by_type[check_type] = []
            results_by_type[check_type].append(result)
        
        # Display results by type
        for check_type, results in results_by_type.items():
            healthy_count = sum(1 for r in results if r.status == HealthStatus.HEALTHY)
            total_count = len(results)
            percentage = (healthy_count / total_count * 100) if total_count > 0 else 0
            
            type_icon = "✅" if percentage == 100 else "⚠️" if percentage > 0 else "❌"
            print(f"{type_icon} {check_type.upper()}: {healthy_count}/{total_count} ({percentage:.0f}%)")
            
            for result in results:
                service_icon = "✅" if result.status == HealthStatus.HEALTHY else "❌"
                response_time = f"{result.response_time_ms:.1f}ms" if result.response_time_ms > 0 else "N/A"
                print(f"    {service_icon} {result.service_name}: {result.status.value} ({response_time})")
                
                if result.error_message and "not installed" not in result.error_message:
                    # Only show connection errors, not missing dependency errors
                    error_msg = result.error_message
                    if len(error_msg) > 80:
                        error_msg = error_msg[:77] + "..."
                    print(f"        {error_msg}")
            print()
        
        return system_health
        
    except Exception as e:
        print(f"❌ Error during health checks: {e}")
        return None


async def demo_connectivity_checks():
    """Demonstrate service connectivity checks."""
    print("🔗 Connectivity Testing")
    print("=" * 25)
    
    config = create_demo_config()
    health_monitor = HealthMonitor(config)
    
    try:
        connectivity_results = await health_monitor.check_service_connectivity()
        
        healthy_count = sum(1 for r in connectivity_results if r.status == HealthStatus.HEALTHY)
        total_count = len(connectivity_results)
        
        print(f"🔍 Tested {total_count} connectivity paths")
        print(f"✅ Healthy: {healthy_count}/{total_count}")
        print()
        
        for result in connectivity_results:
            status_icon = "✅" if result.status == HealthStatus.HEALTHY else "❌"
            response_time = f"{result.response_time_ms:.1f}ms" if result.response_time_ms > 0 else "N/A"
            print(f"{status_icon} {result.service_name}: {result.status.value} ({response_time})")
        
        print()
        
    except Exception as e:
        print(f"❌ Error during connectivity checks: {e}")


def save_demo_results(health_report: dict):
    """Save demo results to file with proper JSON serialization."""
    if health_report:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"health_monitoring_results_{timestamp}.json"
        
        try:
            # Convert the health report to a JSON-serializable format
            serializable_report = json.loads(json.dumps(health_report, default=str))
            
            with open(filename, 'w') as f:
                json.dump(serializable_report, f, indent=2)
            
            print(f"💾 Results saved to: {filename}")
        except Exception as e:
            print(f"⚠️  Could not save results: {e}")


async def main():
    """Run the health monitoring demo."""
    print("🎯 Health Monitoring System - Simple Demo")
    print("=" * 50)
    print()
    
    try:
        # Run basic health checks
        health_report = await demo_basic_health_checks()
        
        # Run connectivity checks
        await demo_connectivity_checks()
        
        # Save results
        if health_report:
            save_demo_results(health_report.to_dict())
        
        print("🎉 Demo completed successfully!")
        print()
        print("💡 Note: Services showing as unhealthy is expected when they're not running.")
        print("   The health monitoring system is working correctly by detecting this.")
        
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())