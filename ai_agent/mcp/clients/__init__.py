"""
MCP Client Implementations

This module contains specific MCP client implementations for different services:
- Confluence MCP client for documentation and wiki content
- JIRA MCP client for issue tracking and project management
- Specialized clients for other integrations
"""

from .confluence_client import ConfluenceMCPClient
from .jira_client import JiraMCPClient

__all__ = [
    "ConfluenceMCPClient",
    "JiraMCPClient"
]