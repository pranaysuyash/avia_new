"""Process management and cleanup utilities."""

import asyncio
import psutil
import signal
import os
import time
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ProcessInfo:
    """Information about a managed process."""
    pid: int
    name: str
    service_name: str
    start_time: float
    command: str
    status: str
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    children: List[int] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []


class ProcessTracker:
    """Tracks and manages system processes."""
    
    def __init__(self):
        self.tracked_processes: Dict[int, ProcessInfo] = {}
        self.service_processes: Dict[str, Set[int]] = {}
        self.orphaned_processes: Set[int] = set()
        
    def register_process(self, pid: int, service_name: str, command: str) -> bool:
        """Register a process for tracking."""
        try:
            process = psutil.Process(pid)
            
            process_info = ProcessInfo(
                pid=pid,
                name=process.name(),
                service_name=service_name,
                start_time=time.time(),
                command=command,
                status=process.status()
            )
            
            self.tracked_processes[pid] = process_info
            
            if service_name not in self.service_processes:
                self.service_processes[service_name] = set()
            self.service_processes[service_name].add(pid)
            
            # Track child processes
            try:
                children = process.children(recursive=True)
                for child in children:
                    process_info.children.append(child.pid)
                    self.tracked_processes[child.pid] = ProcessInfo(
                        pid=child.pid,
                        name=child.name(),
                        service_name=f"{service_name}-child",
                        start_time=time.time(),
                        command=" ".join(child.cmdline()),
                        status=child.status()
                    )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            
            logger.debug(f"Registered process {pid} for service {service_name}")
            return True
            
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.error(f"Failed to register process {pid}: {e}")
            return False
    
    def unregister_process(self, pid: int) -> bool:
        """Unregister a process from tracking."""
        if pid in self.tracked_processes:
            process_info = self.tracked_processes[pid]
            service_name = process_info.service_name
            
            # Remove from service processes
            if service_name in self.service_processes:
                self.service_processes[service_name].discard(pid)
                if not self.service_processes[service_name]:
                    del self.service_processes[service_name]
            
            # Remove child processes
            for child_pid in process_info.children:
                if child_pid in self.tracked_processes:
                    del self.tracked_processes[child_pid]
            
            del self.tracked_processes[pid]
            logger.debug(f"Unregistered process {pid}")
            return True
        
        return False
    
    def get_service_processes(self, service_name: str) -> List[ProcessInfo]:
        """Get all processes for a service."""
        if service_name not in self.service_processes:
            return []
        
        processes = []
        for pid in self.service_processes[service_name]:
            if pid in self.tracked_processes:
                processes.append(self.tracked_processes[pid])
        
        return processes
    
    def update_process_info(self) -> None:
        """Update information for all tracked processes."""
        dead_processes = []
        
        for pid, process_info in self.tracked_processes.items():
            try:
                process = psutil.Process(pid)
                
                # Update process information
                process_info.status = process.status()
                process_info.cpu_percent = process.cpu_percent()
                process_info.memory_percent = process.memory_percent()
                
            except psutil.NoSuchProcess:
                # Process has died
                dead_processes.append(pid)
            except psutil.AccessDenied:
                # Process exists but we can't access it
                process_info.status = "access_denied"
        
        # Clean up dead processes
        for pid in dead_processes:
            self.unregister_process(pid)
    
    def find_orphaned_processes(self) -> List[int]:
        """Find processes that may be orphaned."""
        orphaned = []
        
        # Look for processes that match our service patterns but aren't tracked
        for process in psutil.process_iter(['pid', 'name', 'cmdline', 'ppid']):
            try:
                pid = process.info['pid']
                name = process.info['name']
                cmdline = process.info['cmdline'] or []
                
                # Skip if already tracked
                if pid in self.tracked_processes:
                    continue
                
                # Check if this looks like one of our service processes
                cmdline_str = " ".join(cmdline).lower()
                
                # Common patterns for our services
                service_patterns = [
                    'streamlit', 'uvicorn', 'fastapi', 'react', 'npm', 'node',
                    'electron', 'metro', 'docker', 'postgres', 'redis', 'minio'
                ]
                
                if any(pattern in cmdline_str or pattern in name.lower() for pattern in service_patterns):
                    orphaned.append(pid)
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        self.orphaned_processes.update(orphaned)
        return orphaned
    
    def get_all_processes(self) -> List[ProcessInfo]:
        """Get all tracked processes."""
        return list(self.tracked_processes.values())
    
    def get_process_tree(self, pid: int) -> Dict[str, any]:
        """Get process tree for a given PID."""
        if pid not in self.tracked_processes:
            return {}
        
        try:
            process = psutil.Process(pid)
            process_info = self.tracked_processes[pid]
            
            tree = {
                'pid': pid,
                'name': process_info.name,
                'service': process_info.service_name,
                'status': process_info.status,
                'cpu_percent': process_info.cpu_percent,
                'memory_percent': process_info.memory_percent,
                'children': []
            }
            
            # Add children
            for child_pid in process_info.children:
                if child_pid in self.tracked_processes:
                    child_tree = self.get_process_tree(child_pid)
                    if child_tree:
                        tree['children'].append(child_tree)
            
            return tree
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {}


class ProcessCleaner:
    """Handles graceful shutdown and cleanup of processes."""
    
    def __init__(self, process_tracker: ProcessTracker):
        self.process_tracker = process_tracker
        
    async def cleanup_service_processes(self, service_name: str, timeout: int = 10) -> bool:
        """Clean up all processes for a service."""
        processes = self.process_tracker.get_service_processes(service_name)
        
        if not processes:
            return True
        
        logger.info(f"Cleaning up {len(processes)} processes for service {service_name}")
        
        # First, try graceful shutdown
        for process_info in processes:
            await self._terminate_process_gracefully(process_info.pid, timeout // 2)
        
        # Wait for processes to exit
        await asyncio.sleep(2)
        
        # Check which processes are still running
        remaining_processes = []
        for process_info in processes:
            try:
                process = psutil.Process(process_info.pid)
                if process.is_running():
                    remaining_processes.append(process_info)
            except psutil.NoSuchProcess:
                # Process has exited
                self.process_tracker.unregister_process(process_info.pid)
        
        # Force kill remaining processes
        if remaining_processes:
            logger.warning(f"Force killing {len(remaining_processes)} processes for {service_name}")
            for process_info in remaining_processes:
                await self._kill_process_forcefully(process_info.pid)
        
        # Final cleanup
        await asyncio.sleep(1)
        for process_info in processes:
            self.process_tracker.unregister_process(process_info.pid)
        
        return True
    
    async def _terminate_process_gracefully(self, pid: int, timeout: int = 5) -> bool:
        """Terminate a process gracefully."""
        try:
            process = psutil.Process(pid)
            
            # Send SIGTERM (or equivalent on Windows)
            if os.name == 'nt':
                process.terminate()
            else:
                process.send_signal(signal.SIGTERM)
            
            # Wait for process to exit
            try:
                process.wait(timeout=timeout)
                logger.debug(f"Process {pid} terminated gracefully")
                return True
            except psutil.TimeoutExpired:
                logger.warning(f"Process {pid} did not terminate within {timeout} seconds")
                return False
                
        except psutil.NoSuchProcess:
            # Process already exited
            return True
        except psutil.AccessDenied:
            logger.error(f"Access denied when terminating process {pid}")
            return False
    
    async def _kill_process_forcefully(self, pid: int) -> bool:
        """Force kill a process."""
        try:
            process = psutil.Process(pid)
            
            # Send SIGKILL (or equivalent on Windows)
            if os.name == 'nt':
                process.kill()
            else:
                process.send_signal(signal.SIGKILL)
            
            # Wait a moment for the kill to take effect
            await asyncio.sleep(0.5)
            
            if not process.is_running():
                logger.debug(f"Process {pid} killed forcefully")
                return True
            else:
                logger.error(f"Failed to kill process {pid}")
                return False
                
        except psutil.NoSuchProcess:
            # Process already exited
            return True
        except psutil.AccessDenied:
            logger.error(f"Access denied when killing process {pid}")
            return False
    
    async def cleanup_orphaned_processes(self) -> int:
        """Clean up orphaned processes."""
        orphaned_pids = self.process_tracker.find_orphaned_processes()
        
        if not orphaned_pids:
            return 0
        
        logger.info(f"Found {len(orphaned_pids)} potentially orphaned processes")
        
        cleaned_count = 0
        for pid in orphaned_pids:
            try:
                process = psutil.Process(pid)
                
                # Be more conservative with orphaned processes
                # Only clean up if they look like our service processes
                cmdline = " ".join(process.cmdline()).lower()
                
                # Only clean up processes that are clearly from our services
                if any(pattern in cmdline for pattern in ['streamlit run', 'uvicorn', 'npm start', 'react-scripts']):
                    logger.info(f"Cleaning up orphaned process {pid}: {process.name()}")
                    
                    if await self._terminate_process_gracefully(pid, timeout=5):
                        cleaned_count += 1
                    else:
                        await self._kill_process_forcefully(pid)
                        cleaned_count += 1
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Clear orphaned processes set
        self.process_tracker.orphaned_processes.clear()
        
        logger.info(f"Cleaned up {cleaned_count} orphaned processes")
        return cleaned_count
    
    async def emergency_cleanup(self) -> bool:
        """Emergency cleanup of all tracked processes."""
        logger.warning("Performing emergency cleanup of all processes")
        
        all_processes = self.process_tracker.get_all_processes()
        
        # Kill all processes immediately
        for process_info in all_processes:
            await self._kill_process_forcefully(process_info.pid)
        
        # Clear all tracking
        self.process_tracker.tracked_processes.clear()
        self.process_tracker.service_processes.clear()
        self.process_tracker.orphaned_processes.clear()
        
        logger.info("Emergency cleanup completed")
        return True


class RestartManager:
    """Manages service restart strategies with backoff."""
    
    def __init__(self):
        self.restart_counts: Dict[str, int] = {}
        self.last_restart_times: Dict[str, float] = {}
        self.backoff_multiplier = 2
        self.max_backoff_seconds = 300  # 5 minutes
        self.base_backoff_seconds = 1
        
    def should_restart(self, service_name: str, max_restarts: int) -> bool:
        """Check if a service should be restarted."""
        restart_count = self.restart_counts.get(service_name, 0)
        return restart_count < max_restarts
    
    def calculate_backoff_delay(self, service_name: str) -> float:
        """Calculate backoff delay for service restart."""
        restart_count = self.restart_counts.get(service_name, 0)
        
        # Exponential backoff: base * (multiplier ^ restart_count)
        delay = self.base_backoff_seconds * (self.backoff_multiplier ** restart_count)
        
        # Cap at maximum backoff
        delay = min(delay, self.max_backoff_seconds)
        
        return delay
    
    def record_restart(self, service_name: str) -> None:
        """Record a service restart."""
        current_time = time.time()
        
        self.restart_counts[service_name] = self.restart_counts.get(service_name, 0) + 1
        self.last_restart_times[service_name] = current_time
        
        logger.info(f"Recorded restart for {service_name} (count: {self.restart_counts[service_name]})")
    
    def reset_restart_count(self, service_name: str) -> None:
        """Reset restart count for a service (e.g., after successful run)."""
        if service_name in self.restart_counts:
            del self.restart_counts[service_name]
        if service_name in self.last_restart_times:
            del self.last_restart_times[service_name]
        
        logger.debug(f"Reset restart count for {service_name}")
    
    def get_restart_info(self, service_name: str) -> Dict[str, any]:
        """Get restart information for a service."""
        return {
            'restart_count': self.restart_counts.get(service_name, 0),
            'last_restart_time': self.last_restart_times.get(service_name),
            'next_backoff_delay': self.calculate_backoff_delay(service_name)
        }
    
    def get_all_restart_info(self) -> Dict[str, Dict[str, any]]:
        """Get restart information for all services."""
        info = {}
        
        all_services = set(self.restart_counts.keys()) | set(self.last_restart_times.keys())
        
        for service_name in all_services:
            info[service_name] = self.get_restart_info(service_name)
        
        return info