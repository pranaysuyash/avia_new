"""
Plugin management system for extensible functionality
"""

import logging
import importlib
import inspect
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Type, Callable
import json

logger = logging.getLogger(__name__)


class PluginType(Enum):
    """Types of plugins"""
    ENTITY_EXTRACTION = "entity_extraction"
    PREPROCESSING = "preprocessing"
    POSTPROCESSING = "postprocessing"
    EXPORT = "export"
    INTEGRATION = "integration"
    UI_COMPONENT = "ui_component"


class PluginStatus(Enum):
    """Plugin status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    LOADING = "loading"


@dataclass
class PluginMetadata:
    """Plugin metadata"""
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    dependencies: List[str] = None
    config_schema: Dict[str, Any] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.config_schema is None:
            self.config_schema = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class Plugin(ABC):
    """Abstract base class for all plugins"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.status = PluginStatus.INACTIVE
        self.error_message = None
        self.last_executed = None
    
    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        pass
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the plugin"""
        pass
    
    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """Execute the plugin's main functionality"""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Clean up plugin resources"""
        pass
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration"""
        # Default implementation - can be overridden
        return True
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for UI generation"""
        return self.get_metadata().config_schema
    
    def update_config(self, config: Dict[str, Any]) -> bool:
        """Update plugin configuration"""
        if self.validate_config(config):
            self.config.update(config)
            return True
        return False


class PluginManager:
    """Manages plugin lifecycle and execution"""
    
    def __init__(self, plugin_directory: str = "plugins"):
        self.plugin_directory = plugin_directory
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_configs: Dict[str, Dict[str, Any]] = {}
        self.hooks: Dict[str, List[Callable]] = {}
        
        # Create plugin directory if it doesn't exist
        os.makedirs(plugin_directory, exist_ok=True)
        
        logger.info(f"Plugin manager initialized with directory: {plugin_directory}")
    
    def register_plugin(self, plugin_id: str, plugin: Plugin) -> bool:
        """Register a plugin"""
        try:
            metadata = plugin.get_metadata()
            
            # Validate plugin
            if not self._validate_plugin(plugin):
                logger.error(f"Plugin validation failed for {plugin_id}")
                return False
            
            # Check dependencies
            if not self._check_dependencies(metadata.dependencies):
                logger.error(f"Plugin dependencies not met for {plugin_id}")
                return False
            
            self.plugins[plugin_id] = plugin
            logger.info(f"Registered plugin: {plugin_id} ({metadata.name} v{metadata.version})")
            return True
            
        except Exception as e:
            logger.error(f"Error registering plugin {plugin_id}: {e}")
            return False
    
    def unregister_plugin(self, plugin_id: str) -> bool:
        """Unregister a plugin"""
        if plugin_id in self.plugins:
            plugin = self.plugins[plugin_id]
            
            # Cleanup plugin
            try:
                import asyncio
                asyncio.create_task(plugin.cleanup())
            except Exception as e:
                logger.warning(f"Error during plugin cleanup for {plugin_id}: {e}")
            
            del self.plugins[plugin_id]
            
            # Remove config
            if plugin_id in self.plugin_configs:
                del self.plugin_configs[plugin_id]
            
            logger.info(f"Unregistered plugin: {plugin_id}")
            return True
        
        return False
    
    def get_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """Get a plugin by ID"""
        return self.plugins.get(plugin_id)
    
    def list_plugins(
        self,
        plugin_type: Optional[PluginType] = None,
        status: Optional[PluginStatus] = None
    ) -> List[tuple[str, Plugin]]:
        """List plugins with optional filtering"""
        
        result = []
        for plugin_id, plugin in self.plugins.items():
            metadata = plugin.get_metadata()
            
            # Filter by type
            if plugin_type and metadata.plugin_type != plugin_type:
                continue
            
            # Filter by status
            if status and plugin.status != status:
                continue
            
            result.append((plugin_id, plugin))
        
        return result
    
    async def initialize_plugin(self, plugin_id: str) -> bool:
        """Initialize a plugin"""
        plugin = self.plugins.get(plugin_id)
        if not plugin:
            logger.error(f"Plugin not found: {plugin_id}")
            return False
        
        try:
            plugin.status = PluginStatus.LOADING
            
            # Load configuration
            config = self.plugin_configs.get(plugin_id, {})
            plugin.update_config(config)
            
            # Initialize plugin
            success = await plugin.initialize()
            
            if success:
                plugin.status = PluginStatus.ACTIVE
                plugin.error_message = None
                logger.info(f"Plugin initialized successfully: {plugin_id}")
            else:
                plugin.status = PluginStatus.ERROR
                plugin.error_message = "Initialization failed"
                logger.error(f"Plugin initialization failed: {plugin_id}")
            
            return success
            
        except Exception as e:
            plugin.status = PluginStatus.ERROR
            plugin.error_message = str(e)
            logger.error(f"Error initializing plugin {plugin_id}: {e}")
            return False
    
    async def execute_plugin(self, plugin_id: str, *args, **kwargs) -> Any:
        """Execute a plugin"""
        plugin = self.plugins.get(plugin_id)
        if not plugin:
            raise ValueError(f"Plugin not found: {plugin_id}")
        
        if plugin.status != PluginStatus.ACTIVE:
            raise RuntimeError(f"Plugin {plugin_id} is not active (status: {plugin.status.value})")
        
        try:
            result = await plugin.execute(*args, **kwargs)
            plugin.last_executed = datetime.utcnow()
            return result
            
        except Exception as e:
            plugin.status = PluginStatus.ERROR
            plugin.error_message = str(e)
            logger.error(f"Error executing plugin {plugin_id}: {e}")
            raise
    
    def load_plugins_from_directory(self, directory: Optional[str] = None) -> int:
        """Load plugins from directory"""
        directory = directory or self.plugin_directory
        loaded_count = 0
        
        if not os.path.exists(directory):
            logger.warning(f"Plugin directory does not exist: {directory}")
            return 0
        
        for filename in os.listdir(directory):
            if filename.endswith('.py') and not filename.startswith('__'):
                plugin_name = filename[:-3]  # Remove .py extension
                
                try:
                    # Import plugin module
                    spec = importlib.util.spec_from_file_location(
                        plugin_name,
                        os.path.join(directory, filename)
                    )
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Find plugin classes
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, Plugin) and 
                            obj != Plugin):
                            
                            # Create plugin instance
                            plugin_instance = obj()
                            
                            # Register plugin
                            if self.register_plugin(plugin_name, plugin_instance):
                                loaded_count += 1
                                break
                
                except Exception as e:
                    logger.error(f"Error loading plugin {plugin_name}: {e}")
        
        logger.info(f"Loaded {loaded_count} plugins from {directory}")
        return loaded_count
    
    def save_plugin_config(self, plugin_id: str, config: Dict[str, Any]) -> bool:
        """Save plugin configuration"""
        plugin = self.plugins.get(plugin_id)
        if not plugin:
            return False
        
        if not plugin.validate_config(config):
            logger.error(f"Invalid configuration for plugin {plugin_id}")
            return False
        
        self.plugin_configs[plugin_id] = config
        plugin.update_config(config)
        
        # Save to file
        config_file = os.path.join(self.plugin_directory, f"{plugin_id}_config.json")
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Saved configuration for plugin {plugin_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving config for plugin {plugin_id}: {e}")
            return False
    
    def load_plugin_config(self, plugin_id: str) -> Dict[str, Any]:
        """Load plugin configuration"""
        config_file = os.path.join(self.plugin_directory, f"{plugin_id}_config.json")
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                self.plugin_configs[plugin_id] = config
                logger.info(f"Loaded configuration for plugin {plugin_id}")
                return config
            except Exception as e:
                logger.error(f"Error loading config for plugin {plugin_id}: {e}")
        
        return {}
    
    def register_hook(self, hook_name: str, callback: Callable):
        """Register a hook callback"""
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []
        
        self.hooks[hook_name].append(callback)
        logger.info(f"Registered hook callback for {hook_name}")
    
    async def execute_hooks(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Execute all callbacks for a hook"""
        results = []
        
        if hook_name in self.hooks:
            for callback in self.hooks[hook_name]:
                try:
                    if inspect.iscoroutinefunction(callback):
                        result = await callback(*args, **kwargs)
                    else:
                        result = callback(*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error executing hook {hook_name}: {e}")
        
        return results
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[tuple[str, Plugin]]:
        """Get all plugins of a specific type"""
        return self.list_plugins(plugin_type=plugin_type)
    
    def get_active_plugins(self) -> List[tuple[str, Plugin]]:
        """Get all active plugins"""
        return self.list_plugins(status=PluginStatus.ACTIVE)
    
    def _validate_plugin(self, plugin: Plugin) -> bool:
        """Validate a plugin"""
        try:
            # Check required methods
            required_methods = ['get_metadata', 'initialize', 'execute', 'cleanup']
            for method in required_methods:
                if not hasattr(plugin, method):
                    logger.error(f"Plugin missing required method: {method}")
                    return False
            
            # Validate metadata
            metadata = plugin.get_metadata()
            if not metadata.name or not metadata.version:
                logger.error("Plugin metadata missing name or version")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Plugin validation error: {e}")
            return False
    
    def _check_dependencies(self, dependencies: List[str]) -> bool:
        """Check if plugin dependencies are available"""
        for dependency in dependencies:
            try:
                importlib.import_module(dependency)
            except ImportError:
                logger.error(f"Missing dependency: {dependency}")
                return False
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get plugin system statistics"""
        total_plugins = len(self.plugins)
        active_plugins = len([p for p in self.plugins.values() if p.status == PluginStatus.ACTIVE])
        error_plugins = len([p for p in self.plugins.values() if p.status == PluginStatus.ERROR])
        
        plugin_types = {}
        for plugin in self.plugins.values():
            plugin_type = plugin.get_metadata().plugin_type.value
            plugin_types[plugin_type] = plugin_types.get(plugin_type, 0) + 1
        
        return {
            'total_plugins': total_plugins,
            'active_plugins': active_plugins,
            'inactive_plugins': total_plugins - active_plugins - error_plugins,
            'error_plugins': error_plugins,
            'plugin_types': plugin_types,
            'hooks_registered': len(self.hooks)
        }


# Global plugin manager instance
plugin_manager = PluginManager()