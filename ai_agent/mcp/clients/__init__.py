"""
MCP Client Implementations

This module contains specific MCP client implementations for different services:
- Confluence MCP client for documentation and wiki content
- JIRA MCP client for issue tracking and project management
- Atlassian MCP client for integrated Confluence and Jira operations
- Specialized clients for other integrations
"""

from .confluence_client import ConfluenceMCPClient
from .jira_client import JiraMCPClient
from .atlassian_client import AtlassianMCPClient, AtlassianConfig

__all__ = [
    "ConfluenceMCPClient",
    "JiraMCPClient",
    "AtlassianMCPClient",
    "AtlassianConfig"
]