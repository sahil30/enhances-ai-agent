"""
Base MCP Client Implementation

Provides the foundational MCP client with common functionality for
connecting to and communicating with MCP servers via WebSocket.
"""

import asyncio
import json
import time
import websockets
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)


class MCPConnectionError(Exception):
    """Raised when MCP server connection fails"""
    pass


class MCPRequestError(Exception):
    """Raised when MCP request fails"""
    pass


@dataclass
class MCPConnectionConfig:
    """Configuration for MCP client connections"""
    server_url: str
    access_token: str
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0


class MCPClient:
    """Base MCP client for communicating with MCP servers"""
    
    def __init__(self, config: MCPConnectionConfig):
        self.config = config
        self.websocket = None
        self.request_id = 0
        self.connected = False
        self.connection_time = None
        self.request_count = 0
        self.error_count = 0
        self.logger = structlog.get_logger(f"mcp.{self.__class__.__name__}")
    
    async def connect(self) -> bool:
        """Connect to MCP server with retry logic"""
        if self.connected and self.websocket:
            return True
        
        for attempt in range(self.config.max_retries):
            try:
                self.logger.info(
                    f"Connecting to MCP server (attempt {attempt + 1}/{self.config.max_retries})",
                    server_url=self.config.server_url
                )
                
                self.websocket = await asyncio.wait_for(
                    websockets.connect(
                        self.config.server_url,
                        additional_headers={"Authorization": f"Bearer {self.config.access_token}"}
                    ),
                    timeout=self.config.timeout
                )
                
                self.connected = True
                self.connection_time = time.time()
                
                self.logger.info("Successfully connected to MCP server")
                return True
                
            except Exception as e:
                self.error_count += 1
                self.logger.warning(
                    f"Connection attempt {attempt + 1} failed: {str(e)}",
                    error_type=type(e).__name__
                )
                
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                else:
                    raise MCPConnectionError(f"Failed to connect after {self.config.max_retries} attempts: {str(e)}")
        
        return False
    
    async def disconnect(self) -> None:
        """Disconnect from MCP server"""
        if self.websocket:
            try:
                await self.websocket.close()
                self.logger.info("Disconnected from MCP server")
            except Exception as e:
                self.logger.warning(f"Error during disconnect: {str(e)}")
            finally:
                self.websocket = None
                self.connected = False
                self.connection_time = None
    
    async def send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send request to MCP server with error handling"""
        if not self.connected:
            await self.connect()
        
        self.request_id += 1
        self.request_count += 1
        
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params
        }
        
        try:
            self.logger.debug(
                f"Sending MCP request",
                method=method,
                request_id=self.request_id,
                params_keys=list(params.keys())
            )
            
            await self.websocket.send(json.dumps(request))
            response_data = await asyncio.wait_for(
                self.websocket.recv(),
                timeout=self.config.timeout
            )
            
            response = json.loads(response_data)
            
            if "error" in response:
                self.error_count += 1
                error_msg = response["error"].get("message", "Unknown MCP error")
                self.logger.error(
                    f"MCP request failed",
                    method=method,
                    error=error_msg,
                    request_id=self.request_id
                )
                raise MCPRequestError(f"MCP request failed: {error_msg}")
            
            self.logger.debug(
                f"MCP request successful",
                method=method,
                request_id=self.request_id
            )
            
            return response
            
        except asyncio.TimeoutError:
            self.error_count += 1
            raise MCPRequestError(f"Request timeout after {self.config.timeout}s")
        except websockets.exceptions.ConnectionClosed:
            self.connected = False
            self.websocket = None
            raise MCPConnectionError("WebSocket connection closed unexpectedly")
        except json.JSONDecodeError as e:
            self.error_count += 1
            raise MCPRequestError(f"Invalid JSON response: {str(e)}")
        except Exception as e:
            self.error_count += 1
            raise MCPRequestError(f"Request failed: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on MCP connection"""
        try:
            # Try a simple ping/status request
            response = await self.send_request("server.status", {})
            return {
                "status": "healthy",
                "connected": self.connected,
                "connection_time": self.connection_time,
                "request_count": self.request_count,
                "error_count": self.error_count,
                "error_rate": self.error_count / max(self.request_count, 1),
                "server_response": response.get("result", {})
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": self.connected,
                "error": str(e),
                "request_count": self.request_count,
                "error_count": self.error_count
            }
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        uptime = time.time() - self.connection_time if self.connection_time else 0
        
        return {
            "connected": self.connected,
            "server_url": self.config.server_url,
            "uptime_seconds": uptime,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / max(self.request_count, 1),
            "success_rate": (self.request_count - self.error_count) / max(self.request_count, 1)
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()