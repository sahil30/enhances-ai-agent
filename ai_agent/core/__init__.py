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

# Imports are done lazily to avoid circular dependencies
# Individual modules should be imported directly when needed

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