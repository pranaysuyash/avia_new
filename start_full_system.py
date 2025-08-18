#!/usr/bin/env python3
"""
Full System Startup Script

This script starts all the core services needed for the transcription platform:
- FastAPI backend server
- Streamlit web interface
- PostgreSQL database setup
- Redis cache
- MinIO storage
- React frontend (if available)
"""

import asyncio
import subprocess
import time
import sys
import os
import signal
from pathlib import Path

# Add orchestration to path
sys.path.append('.')

from orchestration.core.orchestrator import ServiceOrchestrator
from orchestration.config.models import SystemConfig, ServiceConfig, ServiceType, EnvironmentConfig
from orchestration.monitoring.health import HealthMonitor

class FullSystemManager:
    def __init__(self):
        self.processes = {}
        self.orchestrator = None
        self.health_monitor = None
        
    def setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
        asyncio.create_task(self.shutdown_all())
    
    async def start_database_services(self):
        """Start database services (PostgreSQL, Redis, MinIO)."""
        print("🗄️  Starting database services...")
        
        # Check if PostgreSQL is running
        try:
            result = subprocess.run(['pg_isready'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ PostgreSQL is already running")
            else:
                print("⚠️  PostgreSQL not running - please start it manually")
        except FileNotFoundError:
            print("⚠️  PostgreSQL not installed - please install and start it")
        
        # Check if Redis is running
        try:
            result = subprocess.run(['redis-cli', 'ping'], capture_output=True, text=True)
            if 'PONG' in result.stdout:
                print("✅ Redis is already running")
            else:
                print("⚠️  Redis not responding - please start it manually")
        except FileNotFoundError:
            print("⚠️  Redis not installed - please install and start it")
        
        # Check if MinIO is running
        try:
            import requests
            response = requests.get('http://localhost:9000/minio/health/live', timeout=5)
            if response.status_code == 200:
                print("✅ MinIO is already running")
            else:
                print("⚠️  MinIO not responding - please start it manually")
        except:
            print("⚠️  MinIO not running - please start it manually")
            print("   You can start MinIO with: minio server ~/minio-data --console-address :9001")
        
        # Create database if it doesn't exist
        await self.setup_database()
    
    async def setup_database(self):
        """Set up the transcription database."""
        print("🔧 Setting up transcription database...")
        try:
            # Try to create the database
            result = subprocess.run([
                'createdb', 'transcription_dev'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Created transcription_dev database")
            elif 'already exists' in result.stderr:
                print("✅ transcription_dev database already exists")
            else:
                print(f"⚠️  Database setup warning: {result.stderr}")
        except FileNotFoundError:
            print("⚠️  PostgreSQL tools not found - please install PostgreSQL")
    
    async def start_backend_services(self):
        """Start backend services (FastAPI, Streamlit)."""
        print("🚀 Starting backend services...")
        
        # Start FastAPI server
        print("  Starting FastAPI server on port 8000...")
        fastapi_process = subprocess.Popen([
            sys.executable, '-m', 'uvicorn', 
            'api.main:app',
            '--host', '0.0.0.0',
            '--port', '8000',
            '--reload'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.processes['fastapi'] = fastapi_process
        
        # Wait a moment for FastAPI to start
        await asyncio.sleep(3)
        
        # Start Streamlit server
        print("  Starting Streamlit server on port 8501...")
        streamlit_process = subprocess.Popen([
            sys.executable, '-m', 'streamlit', 'run',
            'app.py',
            '--server.port', '8501',
            '--server.headless', 'true'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.processes['streamlit'] = streamlit_process
        
        # Wait for services to start
        await asyncio.sleep(5)
    
    async def start_frontend_services(self):
        """Start frontend services if available."""
        print("🌐 Checking for frontend services...")
        
        # Check if React frontend exists
        frontend_path = Path('frontend')
        if frontend_path.exists() and (frontend_path / 'package.json').exists():
            print("  Starting React frontend on port 3000...")
            try:
                frontend_process = subprocess.Popen([
                    'npm', 'start'
                ], cwd='frontend', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.processes['frontend'] = frontend_process
                await asyncio.sleep(3)
            except FileNotFoundError:
                print("⚠️  npm not found - please install Node.js")
        else:
            print("  No React frontend found - skipping")
    
    async def start_health_monitoring(self):
        """Start the health monitoring system."""
        print("🏥 Starting health monitoring system...")
        
        # Create a basic system config for health monitoring
        from orchestration.config.models import (
            SystemConfig, ServiceConfig, ServiceType, EnvironmentConfig,
            BackendConfig, FrontendConfig, InfrastructureConfig
        )
        
        services = {
            "fastapi": ServiceConfig(
                name="fastapi",
                type=ServiceType.BACKEND,
                port=8000,
                health_check_url="http://localhost:8000/health",
                startup_command="uvicorn api.main:app --host 0.0.0.0 --port 8000",
                timeout=30  # Increased timeout
            ),
            "streamlit": ServiceConfig(
                name="streamlit",
                type=ServiceType.BACKEND,
                port=8501,
                health_check_url="http://localhost:8501/_stcore/health",
                startup_command="streamlit run app.py --server.port 8501",
                timeout=30  # Increased timeout
            )
        }
        
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
        
        config = SystemConfig(
            environment="development",
            services=services,
            environments={"development": env_config}
        )
        
        self.health_monitor = HealthMonitor(config, check_interval=30)
        await self.health_monitor.start_monitoring()
    
    async def run_health_check(self):
        """Run a comprehensive health check."""
        if not self.health_monitor:
            print("⚠️  Health monitor not started")
            return
        
        print("\n🔍 Running comprehensive health check...")
        try:
            health_report = await self.health_monitor.get_detailed_health_report()
            
            print(f"\n📊 System Health Status: {health_report['overall_status'].upper()}")
            print(f"   Healthy Services: {health_report['overall_healthy']}/{health_report['overall_total']}")
            
            for check_type, stats in health_report['check_types'].items():
                if stats['total'] > 0:
                    status_icon = "✅" if stats['percentage'] == 100 else "⚠️" if stats['percentage'] > 0 else "❌"
                    print(f"   {status_icon} {check_type.upper()}: {stats['healthy']}/{stats['total']} ({stats['percentage']}%)")
            
            return health_report
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return None
    
    async def monitor_services(self):
        """Monitor running services."""
        print("\n👀 Monitoring services (Ctrl+C to stop)...")
        print("   Health checks will run every 60 seconds...")
        
        check_count = 0
        try:
            while True:
                check_count += 1
                
                # Check process status (less verbose)
                running_services = []
                stopped_services = []
                
                for name, process in self.processes.items():
                    if process.poll() is None:  # Process is still running
                        running_services.append(name)
                    else:
                        stopped_services.append(name)
                
                # Only show status changes or every 5th check
                if stopped_services or check_count % 5 == 1:
                    if running_services:
                        print(f"✅ Running services: {', '.join(running_services)}")
                    if stopped_services:
                        print(f"⚠️  Stopped services: {', '.join(stopped_services)}")
                
                # Run health check every 60 seconds (less frequent)
                if check_count % 2 == 1:  # Every other iteration (60 seconds)
                    print(f"\n🔍 Health check #{check_count // 2 + 1}...")
                    await self.run_health_check()
                
                await asyncio.sleep(30)  # Check every 30 seconds, health check every 60
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping monitoring...")
    
    async def shutdown_all(self):
        """Shutdown all services gracefully."""
        print("\n🛑 Shutting down all services...")
        
        # Stop health monitoring
        if self.health_monitor:
            await self.health_monitor.stop_monitoring()
        
        # Stop all processes
        for name, process in self.processes.items():
            if process.poll() is None:  # Process is still running
                print(f"  Stopping {name}...")
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    print(f"  Force killing {name}...")
                    process.kill()
        
        print("✅ All services stopped")
    
    async def start_all(self):
        """Start all services."""
        print("🎯 Starting Full Transcription Platform System")
        print("=" * 50)
        
        self.setup_signal_handlers()
        
        try:
            # Start services in order
            await self.start_database_services()
            await self.start_backend_services()
            await self.start_frontend_services()
            await self.start_health_monitoring()
            
            print("\n🎉 All services started successfully!")
            print("\n📍 Service URLs:")
            print("  • FastAPI Backend: http://localhost:8000")
            print("  • FastAPI Docs: http://localhost:8000/docs")
            print("  • Streamlit App: http://localhost:8501")
            if 'frontend' in self.processes:
                print("  • React Frontend: http://localhost:3000")
            
            # Run initial health check
            await asyncio.sleep(5)  # Give services time to fully start
            await self.run_health_check()
            
            # Start monitoring
            await self.monitor_services()
            
        except KeyboardInterrupt:
            await self.shutdown_all()
        except Exception as e:
            print(f"❌ Error starting system: {e}")
            await self.shutdown_all()

async def main():
    """Main entry point."""
    manager = FullSystemManager()
    await manager.start_all()

if __name__ == "__main__":
    asyncio.run(main())