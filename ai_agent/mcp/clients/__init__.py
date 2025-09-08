"""
MCP Client Implementations

This module contains specific MCP client implementations for different services:
- Confluence MCP client for documentation and wiki content
- JIRA MCP client for issue tracking and project management
- Atlassian MCP client for integrated Confluence and Jira operations (Docker-based)
- Integrated Atlassian client for direct mcp_atlassian integration
- Specialized clients for other integrations
"""

from .confluence_client import ConfluenceMCPClient
from .jira_client import JiraMCPClient
from .atlassian_client import AtlassianMCPClient, AtlassianConfig
from .integrated_atlassian_client import IntegratedAtlassianClient, IntegratedAtlassianConfig

__all__ = [
    "ConfluenceMCPClient",
    "JiraMCPClient",
    "AtlassianMCPClient",
    "AtlassianConfig",
    "IntegratedAtlassianClient",
    "IntegratedAtlassianConfig"
]