"""
Plugin system for custom entity extraction rules and extensibility
"""

from .plugin_manager import PluginManager, Plugin, PluginType
from .entity_plugin import EntityExtractionPlugin, CustomEntityRule
from .plugin_registry import plugin_registry
from .plugin_ui import render_plugin_settings

__all__ = [
    'PluginManager',
    'Plugin',
    'PluginType',
    'EntityExtractionPlugin',
    'CustomEntityRule',
    'plugin_registry',
    'render_plugin_settings'
]