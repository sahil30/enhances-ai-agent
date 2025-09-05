"""
Core AI Agent Components

This module contains the primary business logic and core functionality:
- Agent orchestration and coordination
- Configuration management  
- AI client integration
- MCP server communication
- Code repository analysis
- Query processing and NLP
"""

from .agent import AIAgent
from .config import Config, load_config
from .ai_client import CustomAIClient
from ..mcp import ConfluenceMCPClient, JiraMCPClient
from .code_reader import CodeRepositoryReader
from .query_processor import NLPProcessor, QueryOptimizer, QueryType, QueryIntent

__all__ = [
    "AIAgent",
    "Config",
    "load_config", 
    "CustomAIClient",
    "ConfluenceMCPClient",
    "JiraMCPClient", 
    "CodeRepositoryReader",
    "NLPProcessor",
    "QueryOptimizer",
    "QueryType",
    "QueryIntent"
]