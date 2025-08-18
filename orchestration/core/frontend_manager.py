"""Frontend service management for React, React Native, and Electron."""

import asyncio
import subprocess
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from ..config.models import ServiceConfig
from .service_manager import ServiceManager
from .types import ServiceInfo, ServiceStatus, ServiceType, StartupResult

logger = logging.getLogger(__name__)


class FrontendServiceManager(ServiceManager):
    """Base class for frontend service management."""
    
    def __init__(self, service_config: ServiceConfig):
        super().__init__(service_config)
        
    async def _check_node_dependencies(self) -> bool:
        """Check if Node.js dependencies are installed."""
        working_dir = Path(self.config.working_directory or ".")
        package_json = working_dir / "package.json"
        node_modules = working_dir / "node_modules"
        
        if not package_json.exists():
            logger.error(f"package.json not found in {working_dir}")
            return False
        
        if not node_modules.exists():
            logger.info(f"node_modules not found, installing dependencies in {working_dir}")
            try:
                result = subprocess.run(
                    ["npm", "install"],
                    cwd=str(working_dir),
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes timeout
                )
                
                if result.returncode != 0:
                    logger.error(f"npm install failed: {result.stderr}")
                    return False
                    
                logger.info("Dependencies installed successfully")
            except subprocess.TimeoutExpired:
                logger.error("npm install timed out")
                return False
            except Exception as e:
                logger.error(f"Error installing dependencies: {e}")
                return False
        
        return True
    
    async def _check_build_tools(self) -> bool:
        """Check if required build tools are available."""
        tools = ["node", "npm"]
        
        for tool in tools:
            try:
                result = subprocess.run(
                    [tool, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode != 0:
                    logger.error(f"{tool} is not available")
                    return False
                else:
                    logger.debug(f"{tool} version: {result.stdout.strip()}")
            except Exception as e:
                logger.error(f"Error checking {tool}: {e}")
                return False
        
        return True


class ReactServiceManager(FrontendServiceManager):
    """Service manager for React applications."""
    
    def __init__(self, service_config: ServiceConfig):
        super().__init__(service_config)
        
    async def start(self) -> StartupResult:
        """Start React development server."""
        logger.info(f"Starting React service: {self.config.name}")
        
        # Check build tools
        if not await self._check_build_tools():
            return StartupResult(
                success=False,
                error_message="Required build tools (Node.js, npm) are not available"
            )
        
        # Check dependencies
        if not await self._check_node_dependencies():
            return StartupResult(
                success=False,
                error_message="Failed to install or verify Node.js dependencies"
            )
        
        # Set React-specific environment variables
        env = os.environ.copy()
        env.update(self.config.environment_variables)
        env.update({
            "PORT": str(self.config.port),
            "BROWSER": "none",  # Don't auto-open browser
            "CI": "false",  # Disable CI mode
            "GENERATE_SOURCEMAP": "true"
        })
        
        # Use Vite if available, otherwise fall back to Create React App
        working_dir = Path(self.config.working_directory or "frontend")
        package_json_path = working_dir / "package.json"
        
        if package_json_path.exists():
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
                
            # Check if using Vite
            if "vite" in package_data.get("devDependencies", {}):
                startup_command = "npm run dev"
                env["VITE_PORT"] = str(self.config.port)
            else:
                startup_command = self.config.startup_command or "npm start"
        else:
            startup_command = self.config.startup_command or "npm start"
        
        # Update the startup command
        self.config.startup_command = startup_command
        
        return await super().start()
    
    async def health_check(self) -> bool:
        """Perform health check for React service."""
        if not self.is_running():
            return False
        
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(
                        f"http://localhost:{self.config.port}",
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 200:
                            self.service_info.health_status = "healthy"
                            return True
                except aiohttp.ClientError:
                    pass
            
            self.service_info.health_status = "unhealthy"
            return False
            
        except ImportError:
            # Fallback to basic process check if aiohttp not available
            return await super().health_check()


class ReactNativeServiceManager(FrontendServiceManager):
    """Service manager for React Native applications."""
    
    def __init__(self, service_config: ServiceConfig):
        super().__init__(service_config)
        
    async def start(self) -> StartupResult:
        """Start React Native Metro bundler."""
        logger.info(f"Starting React Native service: {self.config.name}")
        
        # Check build tools
        if not await self._check_build_tools():
            return StartupResult(
                success=False,
                error_message="Required build tools (Node.js, npm) are not available"
            )
        
        # Check for React Native CLI
        try:
            result = subprocess.run(
                ["npx", "react-native", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                logger.warning("React Native CLI not found, will use npx")
        except Exception:
            logger.warning("Could not verify React Native CLI")
        
        # Check dependencies
        if not await self._check_node_dependencies():
            return StartupResult(
                success=False,
                error_message="Failed to install or verify Node.js dependencies"
            )
        
        # Set React Native specific environment variables
        env = os.environ.copy()
        env.update(self.config.environment_variables)
        env.update({
            "RCT_METRO_PORT": str(self.config.port),
            "REACT_NATIVE_PACKAGER_HOSTNAME": "localhost"
        })
        
        # Use Metro bundler command
        startup_command = self.config.startup_command or "npx react-native start"
        self.config.startup_command = startup_command
        
        return await super().start()
    
    async def health_check(self) -> bool:
        """Perform health check for React Native Metro bundler."""
        if not self.is_running():
            return False
        
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                try:
                    # Check Metro bundler status endpoint
                    async with session.get(
                        f"http://localhost:{self.config.port}/status",
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 200:
                            self.service_info.health_status = "healthy"
                            return True
                except aiohttp.ClientError:
                    pass
            
            self.service_info.health_status = "unhealthy"
            return False
            
        except ImportError:
            # Fallback to basic process check
            return await super().health_check()


class ElectronServiceManager(FrontendServiceManager):
    """Service manager for Electron desktop applications."""
    
    def __init__(self, service_config: ServiceConfig):
        super().__init__(service_config)
        
    async def start(self) -> StartupResult:
        """Start Electron application."""
        logger.info(f"Starting Electron service: {self.config.name}")
        
        # Check build tools
        if not await self._check_build_tools():
            return StartupResult(
                success=False,
                error_message="Required build tools (Node.js, npm) are not available"
            )
        
        # Check for Electron
        working_dir = Path(self.config.working_directory or "desktop_app")
        try:
            result = subprocess.run(
                ["npx", "electron", "--version"],
                cwd=str(working_dir),
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                logger.error("Electron is not available")
                return StartupResult(
                    success=False,
                    error_message="Electron is not available"
                )
            else:
                logger.debug(f"Electron version: {result.stdout.strip()}")
        except Exception as e:
            logger.error(f"Error checking Electron: {e}")
            return StartupResult(
                success=False,
                error_message=f"Error checking Electron: {e}"
            )
        
        # Check dependencies
        if not await self._check_node_dependencies():
            return StartupResult(
                success=False,
                error_message="Failed to install or verify Node.js dependencies"
            )
        
        # Set Electron-specific environment variables
        env = os.environ.copy()
        env.update(self.config.environment_variables)
        env.update({
            "ELECTRON_IS_DEV": "true",
            "ELECTRON_DISABLE_SECURITY_WARNINGS": "true"
        })
        
        # Use Electron command
        startup_command = self.config.startup_command or "npm run electron:dev"
        self.config.startup_command = startup_command
        
        return await super().start()
    
    async def health_check(self) -> bool:
        """Perform health check for Electron application."""
        # For Electron apps, we primarily check if the process is running
        # since they don't typically expose HTTP endpoints
        if not self.is_running():
            return False
        
        try:
            # Check if Electron process is responsive
            if self.service_info.pid:
                import psutil
                try:
                    process = psutil.Process(self.service_info.pid)
                    if process.is_running() and process.status() != psutil.STATUS_ZOMBIE:
                        self.service_info.health_status = "healthy"
                        return True
                except psutil.NoSuchProcess:
                    pass
            
            self.service_info.health_status = "unhealthy"
            return False
            
        except ImportError:
            # Fallback to basic process check
            return await super().health_check()
    
    async def stop(self, timeout: int = 10) -> bool:
        """Stop Electron application with special handling."""
        # Electron apps may need special shutdown handling
        logger.info(f"Stopping Electron service: {self.config.name}")
        
        if self.service_info.status == ServiceStatus.STOPPED:
            return True
        
        # Try graceful shutdown first
        result = await super().stop(timeout)
        
        # If graceful shutdown failed, try to close Electron windows
        if not result and self.process:
            try:
                # Send a quit signal to Electron
                if os.name != 'nt':
                    import signal
                    self.process.send_signal(signal.SIGTERM)
                else:
                    self.process.terminate()
                
                # Wait a bit more for Electron to close
                await asyncio.sleep(3)
                
                if self.process.poll() is None:
                    # Force kill if still running
                    self.process.kill()
                    await asyncio.sleep(1)
                
                self.service_info.status = ServiceStatus.STOPPED
                self.service_info.pid = None
                self.process = None
                
                return True
                
            except Exception as e:
                logger.error(f"Error stopping Electron service: {e}")
                return False
        
        return result


class FrontendServiceFactory:
    """Factory for creating appropriate frontend service managers."""
    
    @staticmethod
    def create_manager(service_config: ServiceConfig) -> FrontendServiceManager:
        """Create appropriate frontend service manager based on configuration."""
        service_name = service_config.name.lower()
        working_dir = Path(service_config.working_directory or ".")
        
        # Determine service type based on name and working directory
        if "react-native" in service_name or "mobile" in service_name:
            return ReactNativeServiceManager(service_config)
        elif "electron" in service_name or "desktop" in service_name:
            return ElectronServiceManager(service_config)
        elif "react" in service_name or "frontend" in service_name:
            return ReactServiceManager(service_config)
        else:
            # Try to detect based on package.json
            package_json = working_dir / "package.json"
            if package_json.exists():
                try:
                    with open(package_json, 'r') as f:
                        package_data = json.load(f)
                    
                    dependencies = {
                        **package_data.get("dependencies", {}),
                        **package_data.get("devDependencies", {})
                    }
                    
                    if "react-native" in dependencies:
                        return ReactNativeServiceManager(service_config)
                    elif "electron" in dependencies:
                        return ElectronServiceManager(service_config)
                    elif "react" in dependencies:
                        return ReactServiceManager(service_config)
                        
                except Exception as e:
                    logger.warning(f"Could not parse package.json: {e}")
            
            # Default to React service manager
            return ReactServiceManager(service_config)