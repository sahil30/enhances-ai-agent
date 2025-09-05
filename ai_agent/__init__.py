"""
AI Agent - Enterprise AI Assistant for Confluence, JIRA, and Code Repository Integration
"""

__version__ = "2.0.0"
__author__ = "AI Agent Team"
__description__ = "Enterprise-grade AI agent for multi-source search and analysis"

# Core imports for easy access
from .core.agent import AIAgent
from .core.config import Config, load_config
from .infrastructure.cache_manager import CacheManager
from .infrastructure.monitoring import performance_monitor
from .api.web_api import app as web_app

__all__ = [
    "AIAgent",
    "Config", 
    "load_config",
    "CacheManager",
    "performance_monitor",
    "web_app"
]