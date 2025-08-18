#!/usr/bin/env python3
"""
Enhanced Health Monitoring System Demo

This demo showcases the comprehensive health monitoring capabilities including:
- HTTP service health checks
- Database connectivity and performance checks
- Cache (Redis) health monitoring
- Storage (MinIO) health checks
- Frontend application health verification
- Service-to-service connectivity testing
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
from orchestration.monitoring.endpoints import HealthEndpoints, StreamlitHealthEndpoints


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
            timeout=10
        ),
        "streamlit": ServiceConfig(
            name="streamlit",
            type=ServiceType.BACKEND,
            port=8501,
            health_check_url="http://localhost:8501/health",
            startup_command="streamlit run app.py --server.port 8501",
            timeout=10
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


async def demo_basic_health_checks():
    """Demonstrate basic health check functionality."""
    print("🏥 Enhanced Health Monitoring System Demo")
    print("=" * 50)
    
    # Create configuration and health monitor
    config = create_demo_config()
    health_monitor = HealthMonitor(config, check_interval=30)
    
    print(f"✅ Initialized health monitor with {len(health_monitor.health_checks)} HTTP checks")
    print(f"✅ Initialized {len(health_monitor.database_checks)} database checks")
    print(f"✅ Initialized {len(health_monitor.cache_checks)} cache checks")
    print(f"✅ Initialized {len(health_monitor.storage_checks)} storage checks")
    print(f"✅ Initialized {len(health_monitor.frontend_checks)} frontend checks")
    print()
    
    # Show configured endpoints
    endpoints = health_monitor.get_health_check_endpoints()
    print("🔗 Configured Health Check Endpoints:")
    for service, endpoint in endpoints.items():
        print(f"  • {service}: {endpoint}")
    print()
    
    # Perform comprehensive health check
    print("🔍 Running comprehensive health checks...")
    start_time = time.time()
    
    try:
        health_report = await health_monitor.get_detailed_health_report()
        check_time = time.time() - start_time
        
        print(f"⏱️  Health checks completed in {check_time:.2f} seconds")
        print()
        
        # Display overall status
        print("📊 Overall System Health:")
        print(f"  Status: {health_report['overall_status'].upper()}")
        print(f"  Healthy Services: {health_report['overall_healthy']}/{health_report['overall_total']}")
        print()
        
        # Display results by check type
        for check_type, stats in health_report['check_types'].items():
            if stats['total'] > 0:
                status_icon = "✅" if stats['percentage'] == 100 else "⚠️" if stats['percentage'] > 0 else "❌"
                print(f"{status_icon} {check_type.upper()} Checks: {stats['healthy']}/{stats['total']} ({stats['percentage']}%)")
                
                for result in stats['results']:
                    status_icon = "✅" if result['status'] == 'healthy' else "⚠️" if result['status'] == 'degraded' else "❌"
                    response_time = f"{result['response_time_ms']:.1f}ms" if result['response_time_ms'] > 0 else "N/A"
                    print(f"    {status_icon} {result['service_name']}: {result['status']} ({response_time})")
                    if result.get('error_message'):
                        print(f"        Error: {result['error_message']}")
                print()
        
        return health_report
        
    except Exception as e:
        print(f"❌ Error during health checks: {e}")
        return None


async def demo_connectivity_checks():
    """Demonstrate service connectivity checks."""
    print("🔗 Service Connectivity Testing")
    print("=" * 30)
    
    config = create_demo_config()
    health_monitor = HealthMonitor(config)
    
    try:
        connectivity_results = await health_monitor.check_service_connectivity()
        
        print(f"🔍 Tested {len(connectivity_results)} connectivity paths:")
        print()
        
        for result in connectivity_results:
            status_icon = "✅" if result.status == HealthStatus.HEALTHY else "❌"
            response_time = f"{result.response_time_ms:.1f}ms" if result.response_time_ms > 0 else "N/A"
            print(f"{status_icon} {result.service_name}: {result.status.value} ({response_time})")
            
            if result.error_message:
                print(f"    Error: {result.error_message}")
            
            if result.details:
                print(f"    Target: {result.details.get('target_url', 'N/A')}")
        
        print()
        
    except Exception as e:
        print(f"❌ Error during connectivity checks: {e}")


async def demo_individual_service_checks():
    """Demonstrate individual service health checks."""
    print("🔍 Individual Service Health Checks")
    print("=" * 35)
    
    config = create_demo_config()
    health_monitor = HealthMonitor(config)
    
    # Test different service types
    services_to_test = ["fastapi", "streamlit", "postgresql", "redis", "minio", "frontend"]
    
    for service_name in services_to_test:
        print(f"Testing {service_name}...")
        try:
            result = await health_monitor.check_specific_service(service_name)
            
            if result:
                status_icon = "✅" if result.status == HealthStatus.HEALTHY else "⚠️" if result.status == HealthStatus.DEGRADED else "❌"
                response_time = f"{result.response_time_ms:.1f}ms" if result.response_time_ms > 0 else "N/A"
                print(f"  {status_icon} Status: {result.status.value} ({response_time})")
                
                if result.error_message:
                    print(f"  ❌ Error: {result.error_message}")
                
                if result.details:
                    try:
                        # Convert any enum values to strings for JSON serialization
                        def convert_enums(obj):
                            if hasattr(obj, 'value'):  # Check if it's an enum
                                return obj.value
                            elif isinstance(obj, dict):
                                return {k: convert_enums(v) for k, v in obj.items()}
                            elif isinstance(obj, list):
                                return [convert_enums(item) for item in obj]
                            else:
                                return obj
                        
                        details_dict = convert_enums(result.details)
                        print(f"  📊 Details: {json.dumps(details_dict, indent=4)}")
                    except Exception as detail_error:
                        print(f"  ❌ Error serializing details: {detail_error}")
            else:
                print(f"  ⚠️  No health check configured for {service_name}")
                
        except Exception as e:
            print(f"  ❌ Error checking {service_name}: {e}")
        
        print()


async def demo_health_endpoints():
    """Demonstrate health check endpoints."""
    print("🌐 Health Check Endpoints Demo")
    print("=" * 30)
    
    config = create_demo_config()
    health_monitor = HealthMonitor(config)
    
    # Create health endpoints
    health_endpoints = HealthEndpoints(health_monitor)
    streamlit_endpoints = StreamlitHealthEndpoints(health_monitor)
    
    print("📡 Available FastAPI Health Endpoints:")
    routes = health_endpoints.router.routes
    for route in routes:
        if hasattr(route, 'path'):
            print(f"  • GET {route.path}")
    print()
    
    # Simulate getting health data for Streamlit
    print("📊 Streamlit Health Data:")
    try:
        health_data = await streamlit_endpoints.get_health_data()
        print(f"  Overall Status: {health_data.get('overall_status', 'unknown')}")
        print(f"  Check Types: {len(health_data.get('check_types', {}))}")
        print(f"  Timestamp: {health_data.get('timestamp', 'N/A')}")
    except Exception as e:
        print(f"  ❌ Error getting Streamlit health data: {e}")
    
    print()


async def demo_health_monitoring_lifecycle():
    """Demonstrate the complete health monitoring lifecycle."""
    print("🔄 Health Monitoring Lifecycle Demo")
    print("=" * 35)
    
    config = create_demo_config()
    health_monitor = HealthMonitor(config, check_interval=5)  # Short interval for demo
    
    print("🚀 Starting health monitoring...")
    await health_monitor.start_monitoring()
    
    # Let it run for a short time
    print("⏳ Monitoring for 15 seconds...")
    await asyncio.sleep(15)
    
    # Get current health
    current_health = health_monitor.get_current_health()
    if current_health:
        print(f"📊 Current System Status: {current_health.overall_status.value}")
        print(f"   Healthy Services: {current_health.healthy_services}/{current_health.total_services}")
    
    # Get health history
    history = health_monitor.get_health_history(hours=1)
    print(f"📈 Health History: {len(history)} checks recorded")
    
    # Get system summary
    summary = health_monitor.get_system_health_summary(hours=1)
    print(f"📋 System Summary:")
    print(f"   Uptime: {summary.get('uptime_percentage', 0)}%")
    print(f"   Total Checks: {summary.get('total_checks', 0)}")
    print(f"   Current Status: {summary.get('current_status', 'unknown')}")
    
    print("🛑 Stopping health monitoring...")
    await health_monitor.stop_monitoring()
    print("✅ Health monitoring stopped")
    print()


def save_demo_results(health_report: dict):
    """Save demo results to file."""
    if health_report:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"health_monitoring_demo_results_{timestamp}.json"
        
        # Custom JSON encoder to handle enums and complex objects
        def enum_serializer(obj):
            if hasattr(obj, 'value'):  # Check if it's an enum
                return obj.value
            elif hasattr(obj, '__dict__'):  # Check if it's a custom object
                # Convert object to dict and recursively serialize
                obj_dict = {}
                for key, value in obj.__dict__.items():
                    try:
                        obj_dict[key] = enum_serializer(value) if hasattr(value, 'value') else value
                    except:
                        obj_dict[key] = str(value)  # Fallback to string representation
                return obj_dict
            elif isinstance(obj, (list, tuple)):
                return [enum_serializer(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: enum_serializer(v) for k, v in obj.items()}
            else:
                # Try to convert to string as last resort
                try:
                    json.dumps(obj)  # Test if it's JSON serializable
                    return obj
                except:
                    return str(obj)
        
        try:
            with open(filename, 'w') as f:
                json.dump(health_report, f, indent=2, default=enum_serializer)
            print(f"💾 Demo results saved to: {filename}")
        except Exception as e:
            print(f"❌ Error saving demo results: {e}")
            # Try to save a simplified version
            try:
                simplified_report = {
                    "timestamp": datetime.now().isoformat(),
                    "overall_status": str(health_report.get('overall_status', 'unknown')),
                    "overall_healthy": health_report.get('overall_healthy', 0),
                    "overall_total": health_report.get('overall_total', 0),
                    "error": "Full report could not be serialized"
                }
                with open(f"simplified_{filename}", 'w') as f:
                    json.dump(simplified_report, f, indent=2)
                print(f"💾 Simplified demo results saved to: simplified_{filename}")
            except Exception as e2:
                print(f"❌ Could not save even simplified results: {e2}")


async def main():
    """Run the complete health monitoring demo."""
    print("🎯 Enhanced Health Monitoring System - Complete Demo")
    print("=" * 60)
    print()
    
    try:
        # Run all demo sections
        health_report = await demo_basic_health_checks()
        await demo_connectivity_checks()
        await demo_individual_service_checks()
        await demo_health_endpoints()
        await demo_health_monitoring_lifecycle()
        
        # Save results
        try:
            if health_report:
                save_demo_results(health_report)
        except Exception as save_error:
            print(f"⚠️  Could not save results: {save_error}")
        
        print("🎉 Health monitoring demo completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())