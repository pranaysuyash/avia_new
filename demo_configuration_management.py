#!/usr/bin/env python3
"""
Demo script for Configuration Management System

This script demonstrates the configuration management capabilities including:
- Loading system configurations
- Environment-specific configurations
- Configuration validation
- Hot-reload capabilities
- Configuration propagation
"""

import asyncio
import logging
import time
from pathlib import Path

from orchestration.config.manager import ConfigurationManager
from orchestration.config.models import ServiceType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_basic_configuration():
    """Demonstrate basic configuration loading and validation."""
    print("\n" + "="*60)
    print("DEMO: Basic Configuration Management")
    print("="*60)
    
    # Initialize configuration manager
    config_manager = ConfigurationManager()
    
    # Load system configuration
    print("\n1. Loading system configuration...")
    system_config = config_manager.load_system_config()
    
    print(f"   Environment: {system_config.environment}")
    print(f"   Services: {list(system_config.services.keys())}")
    print(f"   Environments: {list(system_config.environments.keys())}")
    
    # Validate configuration
    print("\n2. Validating configuration...")
    validation_result = config_manager.validate_configuration(system_config)
    
    if validation_result.is_valid:
        print("   ✅ Configuration is valid")
    else:
        print("   ❌ Configuration has errors:")
        for error in validation_result.errors:
            print(f"      - {error}")
    
    if validation_result.warnings:
        print("   ⚠️  Configuration warnings:")
        for warning in validation_result.warnings:
            print(f"      - {warning}")
    
    return config_manager, system_config


async def demo_environment_configurations(config_manager):
    """Demonstrate environment-specific configurations."""
    print("\n" + "="*60)
    print("DEMO: Environment-Specific Configurations")
    print("="*60)
    
    environments = ["development", "testing", "staging", "production"]
    
    for env in environments:
        print(f"\n{env.upper()} Environment:")
        try:
            env_config = config_manager.load_environment_config(env)
            print(f"   Backend API Port: {env_config.backend.api_port}")
            print(f"   Frontend Port: {env_config.frontend.port}")
            print(f"   Debug Mode: {env_config.backend.debug}")
            print(f"   Workers: {env_config.backend.workers}")
            print(f"   Database: {env_config.infrastructure.postgres['database']}")
        except Exception as e:
            print(f"   ❌ Error loading {env} config: {e}")


async def demo_service_configurations(system_config):
    """Demonstrate service-specific configurations."""
    print("\n" + "="*60)
    print("DEMO: Service Configurations")
    print("="*60)
    
    for service_name, service_config in system_config.services.items():
        print(f"\n{service_name.upper()} Service:")
        print(f"   Type: {service_config.type.value}")
        print(f"   Port: {service_config.port}")
        print(f"   Health Check: {service_config.health_check_url}")
        print(f"   Dependencies: {service_config.dependencies}")
        print(f"   Environment Variables: {len(service_config.environment_variables)} vars")


async def demo_configuration_propagation(config_manager):
    """Demonstrate configuration propagation to services."""
    print("\n" + "="*60)
    print("DEMO: Configuration Propagation")
    print("="*60)
    
    # Propagate configuration to specific services
    target_services = ["fastapi", "streamlit", "react"]
    
    print(f"\nPropagating configuration to services: {target_services}")
    config_manager.propagate_config(target_services)
    
    # Check if service config files were created
    config_path = Path("orchestration/configs")
    for service in target_services:
        service_config_file = config_path / f"{service}.json"
        if service_config_file.exists():
            print(f"   ✅ {service}.json created")
        else:
            print(f"   ❌ {service}.json not found")


async def demo_configuration_watching(config_manager):
    """Demonstrate configuration file watching and hot-reload."""
    print("\n" + "="*60)
    print("DEMO: Configuration Hot-Reload")
    print("="*60)
    
    # Add a change callback
    async def config_change_handler(change):
        print(f"\n🔄 Configuration change detected:")
        print(f"   File: {change.file_path}")
        print(f"   Type: {change.change_type}")
        print(f"   Timestamp: {change.timestamp}")
    
    config_manager.add_change_callback(config_change_handler)
    
    # Start watching
    print("\nStarting configuration file watching...")
    config_manager.start_config_watching()
    
    print("   Configuration watching started")
    print("   Try modifying orchestration/configs/default.yaml to see hot-reload in action")
    print("   Watching for 10 seconds...")
    
    # Wait for potential changes
    await asyncio.sleep(10)
    
    # Stop watching
    config_manager.stop_config_watching()
    print("   Configuration watching stopped")


async def demo_configuration_validation_scenarios():
    """Demonstrate various configuration validation scenarios."""
    print("\n" + "="*60)
    print("DEMO: Configuration Validation Scenarios")
    print("="*60)
    
    from orchestration.config.models import ServiceConfig, SystemConfig
    from orchestration.config.validator import ConfigValidator
    
    validator = ConfigValidator()
    
    # Test valid service configuration
    print("\n1. Testing valid service configuration...")
    valid_service = ServiceConfig(
        name="test-service",
        type=ServiceType.BACKEND,
        port=8080,
        health_check_url="http://localhost:8080/health",
        startup_command="python app.py"
    )
    
    result = validator.validate_service_config(valid_service)
    print(f"   Valid: {result.is_valid}")
    
    # Test invalid service configuration
    print("\n2. Testing invalid service configuration...")
    invalid_service = ServiceConfig(
        name="",  # Invalid: empty name
        type=ServiceType.BACKEND,
        port=70000,  # Invalid: port out of range
        health_check_url="invalid-url",  # Invalid: malformed URL
        startup_command=""  # Invalid: empty command
    )
    
    result = validator.validate_service_config(invalid_service)
    print(f"   Valid: {result.is_valid}")
    if not result.is_valid:
        print("   Errors:")
        for error in result.errors:
            print(f"      - {error}")


async def demo_configuration_schema():
    """Demonstrate configuration schema and structure."""
    print("\n" + "="*60)
    print("DEMO: Configuration Schema")
    print("="*60)
    
    print("\nConfiguration Structure:")
    print("├── Environment Settings")
    print("│   ├── Development")
    print("│   ├── Testing") 
    print("│   ├── Staging")
    print("│   └── Production")
    print("├── Service Definitions")
    print("│   ├── Backend Services (FastAPI, Streamlit)")
    print("│   ├── Frontend Services (React)")
    print("│   ├── Mobile Services (React Native)")
    print("│   ├── Desktop Services (Electron)")
    print("│   └── Infrastructure Services (PostgreSQL, Redis, MinIO)")
    print("├── Logging Configuration")
    print("├── Monitoring Configuration")
    print("├── Testing Configuration")
    print("└── Deployment Configuration")
    
    print("\nSupported Service Types:")
    for service_type in ServiceType:
        print(f"   - {service_type.value}")


async def main():
    """Main demo function."""
    print("🚀 Configuration Management System Demo")
    print("This demo showcases the orchestration system's configuration capabilities")
    
    try:
        # Basic configuration demo
        config_manager, system_config = await demo_basic_configuration()
        
        # Environment configurations demo
        await demo_environment_configurations(config_manager)
        
        # Service configurations demo
        await demo_service_configurations(system_config)
        
        # Configuration propagation demo
        await demo_configuration_propagation(config_manager)
        
        # Configuration validation scenarios
        await demo_configuration_validation_scenarios()
        
        # Configuration schema demo
        await demo_configuration_schema()
        
        # Configuration watching demo (optional - requires user interaction)
        user_input = input("\nWould you like to test configuration hot-reload? (y/n): ")
        if user_input.lower() == 'y':
            await demo_configuration_watching(config_manager)
        
        print("\n" + "="*60)
        print("✅ Configuration Management System Demo Complete!")
        print("="*60)
        print("\nKey Features Demonstrated:")
        print("• Multi-environment configuration support")
        print("• Service-specific configuration management")
        print("• Configuration validation and error reporting")
        print("• Configuration propagation to services")
        print("• Hot-reload capabilities with file watching")
        print("• Comprehensive validation scenarios")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)