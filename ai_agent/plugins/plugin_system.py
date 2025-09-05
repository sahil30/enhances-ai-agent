import asyncio
import importlib
import inspect
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Type
from dataclasses import dataclass
from pathlib import Path
import json
import sys
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


class PluginType(Enum):
    """Types of plugins supported by the system"""
    DATA_SOURCE = "data_source"
    PROCESSOR = "processor"
    FILTER = "filter"
    OUTPUT_FORMAT = "output_format"
    AUTHENTICATOR = "authenticator"
    ANALYZER = "analyzer"


class PluginEvent(Enum):
    """Plugin lifecycle events"""
    PRE_QUERY = "pre_query"
    POST_QUERY = "post_query"
    PRE_SEARCH = "pre_search"
    POST_SEARCH = "post_search"
    PRE_ANALYSIS = "pre_analysis"
    POST_ANALYSIS = "post_analysis"
    ERROR = "error"


@dataclass
class PluginMetadata:
    """Plugin metadata information"""
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    dependencies: List[str] = None
    configuration_schema: Dict[str, Any] = None
    supported_events: List[PluginEvent] = None
    enabled: bool = True

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.supported_events is None:
            self.supported_events = []


@dataclass
class PluginContext:
    """Context passed to plugin methods"""
    query: Optional[str] = None
    results: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = None
    config: Dict[str, Any] = None
    event: Optional[PluginEvent] = None


class BasePlugin(ABC):
    """Base class for all plugins"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.logger = structlog.get_logger(f"plugin.{self.__class__.__name__}")
    
    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        pass
    
    async def initialize(self) -> bool:
        """Initialize plugin (optional override)"""
        self.logger.info(f"Plugin {self.__class__.__name__} initialized")
        return True
    
    async def cleanup(self) -> None:
        """Cleanup plugin resources (optional override)"""
        self.logger.info(f"Plugin {self.__class__.__name__} cleaned up")
    
    async def validate_config(self) -> bool:
        """Validate plugin configuration (optional override)"""
        return True


class DataSourcePlugin(BasePlugin):
    """Base class for data source plugins"""
    
    @abstractmethod
    async def search(self, query: str, options: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search data source and return results"""
        pass
    
    @abstractmethod
    async def get_details(self, item_id: str) -> Dict[str, Any]:
        """Get detailed information about an item"""
        pass
    
    async def test_connection(self) -> bool:
        """Test connection to data source (optional override)"""
        return True


class ProcessorPlugin(BasePlugin):
    """Base class for data processing plugins"""
    
    @abstractmethod
    async def process(self, context: PluginContext) -> PluginContext:
        """Process data and return modified context"""
        pass


class FilterPlugin(BasePlugin):
    """Base class for result filtering plugins"""
    
    @abstractmethod
    async def filter(self, results: List[Dict[str, Any]], criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter results based on criteria"""
        pass


class OutputFormatPlugin(BasePlugin):
    """Base class for output formatting plugins"""
    
    @abstractmethod
    async def format_output(self, data: Any, format_options: Dict[str, Any] = None) -> str:
        """Format data for output"""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Return list of supported format names"""
        pass


class AuthenticatorPlugin(BasePlugin):
    """Base class for authentication plugins"""
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate using provided credentials"""
        pass
    
    @abstractmethod
    async def get_access_token(self) -> Optional[str]:
        """Get access token for API calls"""
        pass


class AnalyzerPlugin(BasePlugin):
    """Base class for analysis plugins"""
    
    @abstractmethod
    async def analyze(self, data: Any, analysis_type: str) -> Dict[str, Any]:
        """Analyze data and return insights"""
        pass


class PluginManager:
    """Manages plugin lifecycle and execution"""
    
    def __init__(self, plugin_directory: str = "./plugins"):
        self.plugin_directory = Path(plugin_directory)
        self.plugins: Dict[str, BasePlugin] = {}
        self.plugin_metadata: Dict[str, PluginMetadata] = {}
        self.event_handlers: Dict[PluginEvent, List[BasePlugin]] = {event: [] for event in PluginEvent}
        self.plugin_configs: Dict[str, Dict[str, Any]] = {}
        
        # Plugin type mappings
        self.plugin_types: Dict[PluginType, List[BasePlugin]] = {ptype: [] for ptype in PluginType}
        
        # Create plugin directory if it doesn't exist
        self.plugin_directory.mkdir(exist_ok=True)
    
    async def load_plugins(self) -> Dict[str, bool]:
        """Load all plugins from plugin directory"""
        results = {}
        
        # Load plugin configurations
        await self._load_plugin_configs()
        
        # Find all plugin files
        plugin_files = list(self.plugin_directory.glob("*.py"))
        plugin_files = [f for f in plugin_files if not f.name.startswith('__')]
        
        logger.info(f"Found {len(plugin_files)} potential plugin files")
        
        for plugin_file in plugin_files:
            plugin_name = plugin_file.stem
            try:
                success = await self._load_plugin(plugin_file, plugin_name)
                results[plugin_name] = success
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_name}: {e}")
                results[plugin_name] = False
        
        # Load built-in plugins
        await self._load_builtin_plugins()
        
        logger.info(f"Plugin loading complete. Loaded: {sum(results.values())}, Failed: {len(results) - sum(results.values())}")
        
        return results
    
    async def _load_plugin(self, plugin_file: Path, plugin_name: str) -> bool:
        """Load individual plugin file"""
        try:
            # Add plugin directory to Python path
            if str(self.plugin_directory) not in sys.path:
                sys.path.insert(0, str(self.plugin_directory))
            
            # Import plugin module
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_file)
            if spec is None or spec.loader is None:
                return False
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find plugin classes in module
            plugin_classes = []
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (issubclass(obj, BasePlugin) and 
                    obj != BasePlugin and 
                    not obj.__name__.startswith('Base')):
                    plugin_classes.append(obj)
            
            if not plugin_classes:
                logger.warning(f"No plugin classes found in {plugin_file}")
                return False
            
            # Instantiate and register plugins
            for plugin_class in plugin_classes:
                plugin_config = self.plugin_configs.get(plugin_name, {})
                plugin_instance = plugin_class(plugin_config)
                
                # Get metadata
                metadata = plugin_instance.get_metadata()
                
                # Validate configuration
                if not await plugin_instance.validate_config():
                    logger.error(f"Configuration validation failed for {metadata.name}")
                    continue
                
                # Initialize plugin
                if await plugin_instance.initialize():
                    self.plugins[metadata.name] = plugin_instance
                    self.plugin_metadata[metadata.name] = metadata
                    
                    # Register by type
                    self.plugin_types[metadata.plugin_type].append(plugin_instance)
                    
                    # Register event handlers
                    for event in metadata.supported_events:
                        self.event_handlers[event].append(plugin_instance)
                    
                    logger.info(f"Successfully loaded plugin: {metadata.name} v{metadata.version}")
                else:
                    logger.error(f"Failed to initialize plugin: {metadata.name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_name}: {e}")
            return False
    
    async def _load_plugin_configs(self):
        """Load plugin configurations from config files"""
        config_file = self.plugin_directory / "plugin_config.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    self.plugin_configs = json.load(f)
                logger.info(f"Loaded plugin configurations from {config_file}")
            except Exception as e:
                logger.error(f"Error loading plugin configs: {e}")
    
    async def _load_builtin_plugins(self):
        """Load built-in plugins"""
        # Example built-in plugins can be defined here
        # For now, we'll skip this but it's a place for default plugins
        pass
    
    async def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a specific plugin"""
        if plugin_name not in self.plugins:
            return False
        
        try:
            plugin = self.plugins[plugin_name]
            metadata = self.plugin_metadata[plugin_name]
            
            # Cleanup plugin
            await plugin.cleanup()
            
            # Remove from registries
            del self.plugins[plugin_name]
            del self.plugin_metadata[plugin_name]
            
            # Remove from type registry
            if plugin in self.plugin_types[metadata.plugin_type]:
                self.plugin_types[metadata.plugin_type].remove(plugin)
            
            # Remove from event handlers
            for event_handlers in self.event_handlers.values():
                if plugin in event_handlers:
                    event_handlers.remove(plugin)
            
            logger.info(f"Successfully unloaded plugin: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error unloading plugin {plugin_name}: {e}")
            return False
    
    async def reload_plugin(self, plugin_name: str) -> bool:
        """Reload a specific plugin"""
        # First unload
        if plugin_name in self.plugins:
            await self.unload_plugin(plugin_name)
        
        # Then reload
        plugin_file = self.plugin_directory / f"{plugin_name}.py"
        if plugin_file.exists():
            return await self._load_plugin(plugin_file, plugin_name)
        
        return False
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[BasePlugin]:
        """Get all plugins of a specific type"""
        return [p for p in self.plugin_types[plugin_type] if p.enabled]
    
    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """Get plugin by name"""
        return self.plugins.get(plugin_name)
    
    async def execute_event_handlers(self, event: PluginEvent, context: PluginContext) -> PluginContext:
        """Execute all plugins registered for an event"""
        handlers = self.event_handlers.get(event, [])
        enabled_handlers = [h for h in handlers if h.enabled]
        
        if not enabled_handlers:
            return context
        
        logger.debug(f"Executing {len(enabled_handlers)} handlers for event {event.value}")
        
        context.event = event
        
        for handler in enabled_handlers:
            try:
                if hasattr(handler, 'handle_event'):
                    context = await handler.handle_event(context)
                elif isinstance(handler, ProcessorPlugin):
                    context = await handler.process(context)
            except Exception as e:
                logger.error(f"Error in event handler {handler.__class__.__name__}: {e}")
                # Continue with other handlers
        
        return context
    
    async def search_data_sources(self, query: str, options: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search all enabled data source plugins"""
        data_sources = self.get_plugins_by_type(PluginType.DATA_SOURCE)
        
        if not data_sources:
            return []
        
        all_results = []
        
        # Execute searches in parallel
        tasks = []
        for ds in data_sources:
            if isinstance(ds, DataSourcePlugin):
                task = self._safe_plugin_call(ds.search, query, options or {})
                tasks.append((ds, task))
        
        # Collect results
        for ds, task in tasks:
            try:
                results = await task
                if results:
                    # Add source metadata to results
                    for result in results:
                        result['_plugin_source'] = ds.get_metadata().name
                    all_results.extend(results)
            except Exception as e:
                logger.error(f"Error in data source {ds.get_metadata().name}: {e}")
        
        return all_results
    
    async def format_output(self, data: Any, format_name: str, options: Dict[str, Any] = None) -> Optional[str]:
        """Format output using specified formatter plugin"""
        formatters = self.get_plugins_by_type(PluginType.OUTPUT_FORMAT)
        
        for formatter in formatters:
            if isinstance(formatter, OutputFormatPlugin):
                if format_name in formatter.get_supported_formats():
                    try:
                        return await formatter.format_output(data, options or {})
                    except Exception as e:
                        logger.error(f"Error in formatter {formatter.get_metadata().name}: {e}")
        
        return None
    
    async def _safe_plugin_call(self, func: Callable, *args, **kwargs) -> Any:
        """Safely call plugin method with error handling"""
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Plugin call failed: {e}")
            return None
    
    def get_plugin_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all plugins"""
        status = {}
        
        for name, plugin in self.plugins.items():
            metadata = self.plugin_metadata[name]
            status[name] = {
                'name': metadata.name,
                'version': metadata.version,
                'type': metadata.plugin_type.value,
                'enabled': plugin.enabled,
                'description': metadata.description,
                'author': metadata.author
            }
        
        return status
    
    async def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a plugin"""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].enabled = True
            logger.info(f"Plugin {plugin_name} enabled")
            return True
        return False
    
    async def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin"""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].enabled = False
            logger.info(f"Plugin {plugin_name} disabled")
            return True
        return False
    
    async def cleanup_all_plugins(self):
        """Cleanup all loaded plugins"""
        logger.info("Cleaning up all plugins")
        
        for plugin_name, plugin in self.plugins.items():
            try:
                await plugin.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up plugin {plugin_name}: {e}")
        
        self.plugins.clear()
        self.plugin_metadata.clear()
        self.plugin_types = {ptype: [] for ptype in PluginType}
        self.event_handlers = {event: [] for event in PluginEvent}


# Example plugin implementations
class ExampleDataSourcePlugin(DataSourcePlugin):
    """Example implementation of a data source plugin"""
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="example_data_source",
            version="1.0.0",
            description="Example data source plugin",
            author="AI Agent Team",
            plugin_type=PluginType.DATA_SOURCE,
            supported_events=[PluginEvent.PRE_SEARCH, PluginEvent.POST_SEARCH]
        )
    
    async def search(self, query: str, options: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        # Example implementation
        return [
            {
                "title": f"Example result for: {query}",
                "content": f"This is example content for query: {query}",
                "source": "example",
                "url": "https://example.com"
            }
        ]
    
    async def get_details(self, item_id: str) -> Dict[str, Any]:
        return {
            "id": item_id,
            "details": f"Detailed information for item {item_id}"
        }


class JSONFormatterPlugin(OutputFormatPlugin):
    """JSON output formatter plugin"""
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="json_formatter",
            version="1.0.0",
            description="JSON output formatter",
            author="AI Agent Team",
            plugin_type=PluginType.OUTPUT_FORMAT
        )
    
    async def format_output(self, data: Any, format_options: Dict[str, Any] = None) -> str:
        indent = format_options.get('indent', 2) if format_options else 2
        return json.dumps(data, indent=indent, default=str)
    
    def get_supported_formats(self) -> List[str]:
        return ["json", "application/json"]


# Global plugin manager instance
plugin_manager = PluginManager()