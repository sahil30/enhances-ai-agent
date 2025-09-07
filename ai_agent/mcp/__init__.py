"""
MCP (Model Context Protocol) Module

This module provides comprehensive MCP server integration capabilities:

- **Base Components**: Core MCP client functionality and utilities
- **Clients**: Specialized implementations for different services
  - Confluence client for documentation and wiki content
  - JIRA client for issue tracking and project management

The MCP system provides:
- WebSocket-based communication with MCP servers
- Structured request/response handling
- Connection pooling and retry logic
- Service-specific formatting and processing
- Health monitoring and diagnostics
"""

# Base MCP functionality
from .base import (
    MCPClient, MCPConnectionError, MCPRequestError,
    format_mcp_response, validate_mcp_params
)

# Specialized client implementations
from .clients import (
    ConfluenceMCPClient,
    JiraMCPClient,
    AtlassianMCPClient,
    AtlassianConfig
)

__all__ = [
    # Base classes and utilities
    "MCPClient",
    "MCPConnectionError", 
    "MCPRequestError",
    "format_mcp_response",
    "validate_mcp_params",
    
    # Client implementations
    "ConfluenceMCPClient",
    "JiraMCPClient",
    "AtlassianMCPClient",
    "AtlassianConfig"
]

__version__ = "1.0.0"