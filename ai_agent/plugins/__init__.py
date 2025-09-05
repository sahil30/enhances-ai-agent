"""
Plugin System

This module contains the extensible plugin architecture:
- Plugin base classes and interfaces
- Plugin manager and lifecycle management
- Built-in plugin implementations
- Plugin discovery and loading
"""

from .plugin_system import (
    BasePlugin, DataSourcePlugin, ProcessorPlugin, FilterPlugin,
    OutputFormatPlugin, AuthenticatorPlugin, AnalyzerPlugin,
    PluginManager, PluginType, PluginEvent, PluginMetadata,
    plugin_manager
)

__all__ = [
    # Base classes
    "BasePlugin", "DataSourcePlugin", "ProcessorPlugin", "FilterPlugin",
    "OutputFormatPlugin", "AuthenticatorPlugin", "AnalyzerPlugin",
    
    # Management
    "PluginManager", "plugin_manager",
    
    # Types and metadata
    "PluginType", "PluginEvent", "PluginMetadata"
]