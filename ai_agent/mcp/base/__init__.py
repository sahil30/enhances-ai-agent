"""
MCP Base Components

This module contains the foundational MCP (Model Context Protocol) infrastructure:
- Base MCP client with common functionality
- Connection management and error handling
- Request/response protocols
- WebSocket communication utilities
"""

from .mcp_base import MCPClient, MCPConnectionError, MCPRequestError
from .utils import format_mcp_response, validate_mcp_params

__all__ = [
    "MCPClient",
    "MCPConnectionError", 
    "MCPRequestError",
    "format_mcp_response",
    "validate_mcp_params"
]