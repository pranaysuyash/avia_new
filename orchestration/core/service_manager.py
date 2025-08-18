"""Service management for individual services."""

import asyncio
import subprocess
import psutil
import time
import signal
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

from ..config.models import ServiceConfig
from .types import ServiceInfo, ServiceStatus, ServiceType, StartupResult
from .process_manager import ProcessTracker, ProcessCleaner, RestartManager

logger = logging.getLogger(__name__)


class ServiceManager:
    """Manages individual service lifecycle."""
    
    def __init__(self, service_config: ServiceConfig, process_tracker: Optional[ProcessTracker] = None):
        self.config = service_config
        self.service_info = ServiceInfo(
            name=service_config.name,
            service_type=service_config.type,
            status=ServiceStatus.STOPPED
        )
        self.process: Optional[subprocess.Popen] = None
        self.restart_attempts = 0
        self.max_restart_attempts = service_config.max_restarts
        self.process_tracker = process_tracker or ProcessTracker()
        self.process_cleaner = ProcessCleaner(self.process_tracker)
        self.restart_manager = RestartManager()
        
    async def start(self) -> StartupResult:
        """Start the service."""
        if self.service_info.status in [ServiceStatus.RUNNING, ServiceStatus.STARTING]:
            return StartupResult(
                success=False,
                error_message=f"Service {self.config.name} is already {self.service_info.status.value}"
            )
            
        logger.info(f"Starting service: {self.config.name}")
        self.service_info.status = ServiceStatus.STARTING
        
        try:
            # Prepare environment
            env = os.environ.copy()
            env.update(self.config.environment_variables)
            
            # Prepare working directory
            working_dir = self.config.working_directory or "."
            working_path = Path(working_dir).resolve()
            
            if not working_path.exists():
                return StartupResult(
                    success=False,
                    error_message=f"Working directory does not exist: {working_path}"
                )
            
            # Start the process
            self.process = subprocess.Popen(
                self.config.startup_command.split(),
                cwd=str(working_path),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            # Wait a moment to check if process started successfully
            await asyncio.sleep(1)
            
            if self.process.poll() is not None:
                # Process exited immediately
                stdout, stderr = self.process.communicate()
                error_msg = f"Service failed to start: {stderr.decode() if stderr else 'Unknown error'}"
                
                self.service_info.status = ServiceStatus.FAILED
                self.service_info.error_message = error_msg
                
                return StartupResult(
                    success=False,
                    error_message=error_msg
                )
            
            # Process started successfully
            self.service_info.pid = self.process.pid
            self.service_info.port = self.config.port
            self.service_info.start_time = time.time()
            self.service_info.status = ServiceStatus.RUNNING
            self.service_info.error_message = None
            
            # Register process for tracking
            self.process_tracker.register_process(
                self.process.pid,
                self.config.name,
                self.config.startup_command
            )
            
            logger.info(f"Service {self.config.name} started successfully (PID: {self.process.pid})")
            
            return StartupResult(
                success=True,
                service_info=self.service_info,
                pid=self.process.pid
            )
            
        except Exception as e:
            error_msg = f"Failed to start service {self.config.name}: {str(e)}"
            logger.error(error_msg)
            
            self.service_info.status = ServiceStatus.FAILED
            self.service_info.error_message = error_msg
            
            return StartupResult(
                success=False,
                error_message=error_msg
            )
    
    async def stop(self, timeout: int = 10) -> bool:
        """Stop the service gracefully."""
        if self.service_info.status == ServiceStatus.STOPPED:
            return True
            
        if self.service_info.status == ServiceStatus.STOPPING:
            return False
            
        logger.info(f"Stopping service: {self.config.name}")
        self.service_info.status = ServiceStatus.STOPPING
        
        try:
            if self.process and self.process.poll() is None:
                # Try graceful shutdown first
                if os.name != 'nt':
                    # Unix-like systems
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                else:
                    # Windows
                    self.process.terminate()
                
                # Wait for graceful shutdown
                try:
                    await asyncio.wait_for(
                        asyncio.create_task(self._wait_for_process_exit()),
                        timeout=timeout
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"Service {self.config.name} did not stop gracefully, forcing shutdown")
                    
                    # Force kill
                    if os.name != 'nt':
                        os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                    else:
                        self.process.kill()
                    
                    # Wait a bit more
                    await asyncio.sleep(2)
            
            # Unregister process from tracking
            if self.service_info.pid:
                self.process_tracker.unregister_process(self.service_info.pid)
            
            self.service_info.status = ServiceStatus.STOPPED
            self.service_info.pid = None
            self.process = None
            
            logger.info(f"Service {self.config.name} stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping service {self.config.name}: {e}")
            self.service_info.status = ServiceStatus.FAILED
            self.service_info.error_message = str(e)
            return False
    
    async def _wait_for_process_exit(self):
        """Wait for process to exit."""
        while self.process and self.process.poll() is None:
            await asyncio.sleep(0.1)
    
    async def restart(self) -> StartupResult:
        """Restart the service."""
        logger.info(f"Restarting service: {self.config.name}")
        
        # Stop the service first
        await self.stop()
        
        # Wait a moment before restarting
        await asyncio.sleep(2)
        
        # Start the service
        result = await self.start()
        
        if result.success:
            self.restart_attempts = 0
        else:
            self.restart_attempts += 1
            
        return result
    
    def is_running(self) -> bool:
        """Check if service is currently running."""
        if self.process is None:
            return False
            
        # Check if process is still alive
        if self.process.poll() is not None:
            # Process has exited
            self.service_info.status = ServiceStatus.STOPPED
            self.service_info.pid = None
            self.process = None
            return False
            
        return self.service_info.status == ServiceStatus.RUNNING
    
    def get_status(self) -> ServiceInfo:
        """Get current service status."""
        # Update status based on actual process state
        if self.process:
            if self.process.poll() is not None:
                # Process has exited
                self.service_info.status = ServiceStatus.STOPPED
                self.service_info.pid = None
                self.process = None
        
        return self.service_info
    
    async def health_check(self) -> bool:
        """Perform health check on the service."""
        if not self.is_running():
            self.service_info.health_status = "stopped"
            return False
        
        try:
            # For services with health check URLs, we'll use the health monitor
            # For now, just check if process is responsive
            if self.service_info.pid:
                try:
                    process = psutil.Process(self.service_info.pid)
                    if process.is_running():
                        self.service_info.health_status = "healthy"
                        self.service_info.last_health_check = time.time()
                        return True
                except psutil.NoSuchProcess:
                    pass
            
            self.service_info.health_status = "unhealthy"
            return False
            
        except Exception as e:
            logger.error(f"Health check failed for {self.config.name}: {e}")
            self.service_info.health_status = "error"
            self.service_info.error_message = str(e)
            return False
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """Get resource usage for the service."""
        if not self.service_info.pid:
            return {}
        
        try:
            process = psutil.Process(self.service_info.pid)
            
            return {
                'cpu_percent': process.cpu_percent(),
                'memory_info': process.memory_info()._asdict(),
                'memory_percent': process.memory_percent(),
                'num_threads': process.num_threads(),
                'create_time': process.create_time(),
                'status': process.status()
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {}


class BackendServiceManager(ServiceManager):
    """Specialized manager for backend services (FastAPI, Streamlit)."""
    
    def __init__(self, service_config: ServiceConfig):
        super().__init__(service_config)
        
    async def start(self) -> StartupResult:
        """Start backend service with specific configurations."""
        # Add backend-specific environment variables
        if self.config.name == "fastapi":
            self.config.environment_variables.update({
                "UVICORN_HOST": "0.0.0.0",
                "UVICORN_PORT": str(self.config.port),
                "UVICORN_RELOAD": "true" if self.config.environment_variables.get("DEBUG", "false").lower() == "true" else "false"
            })
        elif self.config.name == "streamlit":
            self.config.environment_variables.update({
                "STREAMLIT_SERVER_PORT": str(self.config.port),
                "STREAMLIT_SERVER_ADDRESS": "0.0.0.0"
            })
        
        return await super().start()


class InfrastructureServiceManager(ServiceManager):
    """Specialized manager for infrastructure services (PostgreSQL, Redis, MinIO)."""
    
    def __init__(self, service_config: ServiceConfig):
        super().__init__(service_config)
        
    async def start(self) -> StartupResult:
        """Start infrastructure service with Docker if needed."""
        # Check if this is a Docker-based service
        if "docker" in self.config.startup_command.lower():
            # For Docker services, we need to handle container management
            return await self._start_docker_service()
        else:
            return await super().start()
    
    async def _start_docker_service(self) -> StartupResult:
        """Start a Docker-based infrastructure service."""
        logger.info(f"Starting Docker service: {self.config.name}")
        
        try:
            # Check if Docker is available
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                return StartupResult(
                    success=False,
                    error_message="Docker is not available or not installed"
                )
            
            # Check if container already exists and is running
            check_cmd = f"docker ps -q -f name={self.config.name}"
            result = subprocess.run(check_cmd.split(), capture_output=True, text=True)
            
            if result.stdout.strip():
                logger.info(f"Docker container {self.config.name} is already running")
                self.service_info.status = ServiceStatus.RUNNING
                return StartupResult(success=True, service_info=self.service_info)
            
            # Start the Docker container
            self.process = subprocess.Popen(
                self.config.startup_command.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for container to start
            await asyncio.sleep(3)
            
            # Check if container is running
            result = subprocess.run(check_cmd.split(), capture_output=True, text=True)
            if result.stdout.strip():
                self.service_info.status = ServiceStatus.RUNNING
                self.service_info.port = self.config.port
                self.service_info.start_time = time.time()
                
                logger.info(f"Docker service {self.config.name} started successfully")
                return StartupResult(success=True, service_info=self.service_info)
            else:
                return StartupResult(
                    success=False,
                    error_message=f"Failed to start Docker container {self.config.name}"
                )
                
        except Exception as e:
            error_msg = f"Failed to start Docker service {self.config.name}: {str(e)}"
            logger.error(error_msg)
            return StartupResult(success=False, error_message=error_msg)
    
    async def stop(self, timeout: int = 10) -> bool:
        """Stop infrastructure service."""
        if "docker" in self.config.startup_command.lower():
            return await self._stop_docker_service()
        else:
            return await super().stop(timeout)
    
    async def _stop_docker_service(self) -> bool:
        """Stop Docker-based infrastructure service."""
        try:
            # Stop the container
            stop_cmd = f"docker stop {self.config.name}"
            result = subprocess.run(stop_cmd.split(), capture_output=True, text=True)
            
            if result.returncode == 0:
                self.service_info.status = ServiceStatus.STOPPED
                logger.info(f"Docker service {self.config.name} stopped successfully")
                return True
            else:
                logger.error(f"Failed to stop Docker service {self.config.name}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error stopping Docker service {self.config.name}: {e}")
            return False