"""
Full-Stack Testing and Deployment Orchestration System

This package provides comprehensive orchestration, testing, and deployment
capabilities for multi-platform applications.
"""

__version__ = "1.0.0"
__author__ = "Full-Stack Testing Team"

from .core.orchestrator import ServiceOrchestrator
from .config.manager import ConfigurationManager
from .monitoring.health import HealthMonitor
# from .testing.suite import TestSuite  # TODO: Implement testing module

__all__ = [
    "ServiceOrchestrator",
    "ConfigurationManager", 
    "HealthMonitor",
    # "TestSuite"
]