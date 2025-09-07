"""
Atlassian MCP Client

Provides comprehensive integration with the mcp-atlassian server for both
Confluence and Jira operations. This client uses the Docker-based mcp-atlassian
server to perform operations on Atlassian Cloud and Server/Data Center instances.
"""

import asyncio
import json
import subprocess
import tempfile
import os
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import structlog

from ..base.mcp_base import MCPClient, MCPConnectionConfig, MCPConnectionError, MCPRequestError

logger = structlog.get_logger(__name__)


@dataclass
class AtlassianConfig:
    """Configuration for Atlassian MCP integration"""
    
    # Confluence settings
    confluence_url: Optional[str] = None
    confluence_username: Optional[str] = None
    confluence_api_token: Optional[str] = None
    confluence_personal_token: Optional[str] = None
    confluence_ssl_verify: bool = True
    confluence_spaces_filter: Optional[str] = None
    confluence_custom_headers: Optional[str] = None
    
    # Jira settings  
    jira_url: Optional[str] = None
    jira_username: Optional[str] = None
    jira_api_token: Optional[str] = None
    jira_personal_token: Optional[str] = None
    jira_ssl_verify: bool = True
    jira_projects_filter: Optional[str] = None
    jira_custom_headers: Optional[str] = None
    
    # OAuth settings (for Cloud)
    oauth_cloud_id: Optional[str] = None
    oauth_client_id: Optional[str] = None
    oauth_client_secret: Optional[str] = None
    oauth_redirect_uri: Optional[str] = None
    oauth_scope: Optional[str] = None
    oauth_access_token: Optional[str] = None
    
    # Server settings
    docker_image: str = "ghcr.io/sooperset/mcp-atlassian:latest"
    read_only_mode: bool = False
    enabled_tools: Optional[str] = None
    mcp_verbose: bool = False
    mcp_logging_stdout: bool = True
    
    # Proxy settings
    http_proxy: Optional[str] = None
    https_proxy: Optional[str] = None
    no_proxy: Optional[str] = None


class AtlassianMCPClient:
    """
    Atlassian MCP Client for integration with mcp-atlassian server
    
    This client manages the Docker-based mcp-atlassian server and provides
    a Python interface for Confluence and Jira operations.
    """
    
    def __init__(self, config: AtlassianConfig):
        self.config = config
        self.process = None
        self.logger = structlog.get_logger("mcp.atlassian")
        self.running = False
        
    def _build_docker_args(self) -> List[str]:
        """Build Docker arguments from configuration"""
        args = ["docker", "run", "--rm", "-i"]
        
        # Add environment variables
        env_vars = []
        
        # Confluence settings
        if self.config.confluence_url:
            env_vars.extend(["-e", "CONFLUENCE_URL"])
        if self.config.confluence_username:
            env_vars.extend(["-e", "CONFLUENCE_USERNAME"])
        if self.config.confluence_api_token:
            env_vars.extend(["-e", "CONFLUENCE_API_TOKEN"])
        if self.config.confluence_personal_token:
            env_vars.extend(["-e", "CONFLUENCE_PERSONAL_TOKEN"])
        if not self.config.confluence_ssl_verify:
            env_vars.extend(["-e", "CONFLUENCE_SSL_VERIFY"])
        if self.config.confluence_spaces_filter:
            env_vars.extend(["-e", "CONFLUENCE_SPACES_FILTER"])
        if self.config.confluence_custom_headers:
            env_vars.extend(["-e", "CONFLUENCE_CUSTOM_HEADERS"])
            
        # Jira settings
        if self.config.jira_url:
            env_vars.extend(["-e", "JIRA_URL"])
        if self.config.jira_username:
            env_vars.extend(["-e", "JIRA_USERNAME"])
        if self.config.jira_api_token:
            env_vars.extend(["-e", "JIRA_API_TOKEN"])
        if self.config.jira_personal_token:
            env_vars.extend(["-e", "JIRA_PERSONAL_TOKEN"])
        if not self.config.jira_ssl_verify:
            env_vars.extend(["-e", "JIRA_SSL_VERIFY"])
        if self.config.jira_projects_filter:
            env_vars.extend(["-e", "JIRA_PROJECTS_FILTER"])
        if self.config.jira_custom_headers:
            env_vars.extend(["-e", "JIRA_CUSTOM_HEADERS"])
            
        # OAuth settings
        if self.config.oauth_cloud_id:
            env_vars.extend(["-e", "ATLASSIAN_OAUTH_CLOUD_ID"])
        if self.config.oauth_client_id:
            env_vars.extend(["-e", "ATLASSIAN_OAUTH_CLIENT_ID"])
        if self.config.oauth_client_secret:
            env_vars.extend(["-e", "ATLASSIAN_OAUTH_CLIENT_SECRET"])
        if self.config.oauth_redirect_uri:
            env_vars.extend(["-e", "ATLASSIAN_OAUTH_REDIRECT_URI"])
        if self.config.oauth_scope:
            env_vars.extend(["-e", "ATLASSIAN_OAUTH_SCOPE"])
        if self.config.oauth_access_token:
            env_vars.extend(["-e", "ATLASSIAN_OAUTH_ACCESS_TOKEN"])
            
        # Server configuration
        if self.config.read_only_mode:
            env_vars.extend(["-e", "READ_ONLY_MODE"])
        if self.config.enabled_tools:
            env_vars.extend(["-e", "ENABLED_TOOLS"])
        if self.config.mcp_verbose:
            env_vars.extend(["-e", "MCP_VERBOSE"])
        if self.config.mcp_logging_stdout:
            env_vars.extend(["-e", "MCP_LOGGING_STDOUT"])
            
        # Proxy settings
        if self.config.http_proxy:
            env_vars.extend(["-e", "HTTP_PROXY"])
        if self.config.https_proxy:
            env_vars.extend(["-e", "HTTPS_PROXY"])
        if self.config.no_proxy:
            env_vars.extend(["-e", "NO_PROXY"])
        
        args.extend(env_vars)
        args.append(self.config.docker_image)
        
        return args
    
    def _build_environment(self) -> Dict[str, str]:
        """Build environment variables dictionary"""
        env = {}
        
        # Confluence settings
        if self.config.confluence_url:
            env["CONFLUENCE_URL"] = self.config.confluence_url
        if self.config.confluence_username:
            env["CONFLUENCE_USERNAME"] = self.config.confluence_username
        if self.config.confluence_api_token:
            env["CONFLUENCE_API_TOKEN"] = self.config.confluence_api_token
        if self.config.confluence_personal_token:
            env["CONFLUENCE_PERSONAL_TOKEN"] = self.config.confluence_personal_token
        if not self.config.confluence_ssl_verify:
            env["CONFLUENCE_SSL_VERIFY"] = "false"
        if self.config.confluence_spaces_filter:
            env["CONFLUENCE_SPACES_FILTER"] = self.config.confluence_spaces_filter
        if self.config.confluence_custom_headers:
            env["CONFLUENCE_CUSTOM_HEADERS"] = self.config.confluence_custom_headers
            
        # Jira settings
        if self.config.jira_url:
            env["JIRA_URL"] = self.config.jira_url
        if self.config.jira_username:
            env["JIRA_USERNAME"] = self.config.jira_username
        if self.config.jira_api_token:
            env["JIRA_API_TOKEN"] = self.config.jira_api_token
        if self.config.jira_personal_token:
            env["JIRA_PERSONAL_TOKEN"] = self.config.jira_personal_token
        if not self.config.jira_ssl_verify:
            env["JIRA_SSL_VERIFY"] = "false"
        if self.config.jira_projects_filter:
            env["JIRA_PROJECTS_FILTER"] = self.config.jira_projects_filter
        if self.config.jira_custom_headers:
            env["JIRA_CUSTOM_HEADERS"] = self.config.jira_custom_headers
            
        # OAuth settings
        if self.config.oauth_cloud_id:
            env["ATLASSIAN_OAUTH_CLOUD_ID"] = self.config.oauth_cloud_id
        if self.config.oauth_client_id:
            env["ATLASSIAN_OAUTH_CLIENT_ID"] = self.config.oauth_client_id
        if self.config.oauth_client_secret:
            env["ATLASSIAN_OAUTH_CLIENT_SECRET"] = self.config.oauth_client_secret
        if self.config.oauth_redirect_uri:
            env["ATLASSIAN_OAUTH_REDIRECT_URI"] = self.config.oauth_redirect_uri
        if self.config.oauth_scope:
            env["ATLASSIAN_OAUTH_SCOPE"] = self.config.oauth_scope
        if self.config.oauth_access_token:
            env["ATLASSIAN_OAUTH_ACCESS_TOKEN"] = self.config.oauth_access_token
            
        # Server configuration
        if self.config.read_only_mode:
            env["READ_ONLY_MODE"] = "true"
        if self.config.enabled_tools:
            env["ENABLED_TOOLS"] = self.config.enabled_tools
        if self.config.mcp_verbose:
            env["MCP_VERBOSE"] = "true"
        if self.config.mcp_logging_stdout:
            env["MCP_LOGGING_STDOUT"] = "true"
            
        # Proxy settings
        if self.config.http_proxy:
            env["HTTP_PROXY"] = self.config.http_proxy
        if self.config.https_proxy:
            env["HTTPS_PROXY"] = self.config.https_proxy
        if self.config.no_proxy:
            env["NO_PROXY"] = self.config.no_proxy
        
        return env
    
    async def start_server(self) -> bool:
        """Start the mcp-atlassian Docker container"""
        if self.running and self.process:
            return True
            
        try:
            docker_args = self._build_docker_args()
            env_dict = self._build_environment()
            
            self.logger.info("Starting mcp-atlassian server", docker_image=self.config.docker_image)
            
            # Merge with system environment
            full_env = os.environ.copy()
            full_env.update(env_dict)
            
            self.process = await asyncio.create_subprocess_exec(
                *docker_args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=full_env
            )
            
            self.running = True
            self.logger.info("mcp-atlassian server started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start mcp-atlassian server: {str(e)}")
            raise MCPConnectionError(f"Failed to start mcp-atlassian server: {str(e)}")
    
    async def stop_server(self) -> None:
        """Stop the mcp-atlassian Docker container"""
        if self.process:
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=10)
                self.logger.info("mcp-atlassian server stopped")
            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()
                self.logger.warning("mcp-atlassian server force killed")
            except Exception as e:
                self.logger.error(f"Error stopping server: {str(e)}")
            finally:
                self.process = None
                self.running = False
    
    async def send_mcp_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send MCP request to the server"""
        if not self.running or not self.process:
            await self.start_server()
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }
        
        try:
            request_json = json.dumps(request) + "\n"
            
            self.logger.debug(f"Sending MCP request: {method}", params=params)
            
            self.process.stdin.write(request_json.encode())
            await self.process.stdin.drain()
            
            # Read response
            response_data = await self.process.stdout.readline()
            response = json.loads(response_data.decode().strip())
            
            if "error" in response:
                error_msg = response["error"].get("message", "Unknown error")
                self.logger.error(f"MCP request failed: {error_msg}", method=method)
                raise MCPRequestError(f"MCP request failed: {error_msg}")
            
            self.logger.debug(f"MCP request successful: {method}")
            return response.get("result", {})
            
        except json.JSONDecodeError as e:
            raise MCPRequestError(f"Invalid JSON response: {str(e)}")
        except Exception as e:
            raise MCPRequestError(f"Request failed: {str(e)}")
    
    # Confluence Methods
    async def confluence_search(self, query: str, space_keys: Optional[List[str]] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Search Confluence content"""
        params = {
            "cql": query,
            "limit": limit
        }
        if space_keys:
            params["space_keys"] = space_keys
            
        result = await self.send_mcp_request("confluence_search", params)
        return result.get("pages", [])
    
    async def confluence_get_page(self, page_id: str, expand: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get Confluence page content"""
        params = {"page_id": page_id}
        if expand:
            params["expand"] = expand
            
        return await self.send_mcp_request("confluence_get_page", params)
    
    async def confluence_create_page(self, space_key: str, title: str, content: str, 
                                   parent_id: Optional[str] = None) -> Dict[str, Any]:
        """Create new Confluence page"""
        params = {
            "space_key": space_key,
            "title": title,
            "content": content
        }
        if parent_id:
            params["parent_id"] = parent_id
            
        return await self.send_mcp_request("confluence_create_page", params)
    
    async def confluence_update_page(self, page_id: str, title: str, content: str, 
                                   version_number: int) -> Dict[str, Any]:
        """Update existing Confluence page"""
        params = {
            "page_id": page_id,
            "title": title,
            "content": content,
            "version_number": version_number
        }
        return await self.send_mcp_request("confluence_update_page", params)
    
    # Jira Methods
    async def jira_search(self, jql: str, fields: Optional[List[str]] = None, 
                         max_results: int = 50) -> List[Dict[str, Any]]:
        """Search Jira issues using JQL"""
        params = {
            "jql": jql,
            "max_results": max_results
        }
        if fields:
            params["fields"] = fields
            
        result = await self.send_mcp_request("jira_search", params)
        return result.get("issues", [])
    
    async def jira_get_issue(self, issue_key: str, expand: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get Jira issue details"""
        params = {"issue_key": issue_key}
        if expand:
            params["expand"] = expand
            
        return await self.send_mcp_request("jira_get_issue", params)
    
    async def jira_create_issue(self, project_key: str, summary: str, description: str,
                               issue_type: str = "Task", **kwargs) -> Dict[str, Any]:
        """Create new Jira issue"""
        params = {
            "project_key": project_key,
            "summary": summary,
            "description": description,
            "issue_type": issue_type,
            **kwargs
        }
        return await self.send_mcp_request("jira_create_issue", params)
    
    async def jira_update_issue(self, issue_key: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing Jira issue"""
        params = {
            "issue_key": issue_key,
            "fields": fields
        }
        return await self.send_mcp_request("jira_update_issue", params)
    
    async def jira_add_comment(self, issue_key: str, comment: str) -> Dict[str, Any]:
        """Add comment to Jira issue"""
        params = {
            "issue_key": issue_key,
            "comment": comment
        }
        return await self.send_mcp_request("jira_add_comment", params)
    
    async def jira_transition_issue(self, issue_key: str, transition_name: str,
                                   comment: Optional[str] = None) -> Dict[str, Any]:
        """Transition Jira issue to new status"""
        params = {
            "issue_key": issue_key,
            "transition_name": transition_name
        }
        if comment:
            params["comment"] = comment
            
        return await self.send_mcp_request("jira_transition_issue", params)
    
    async def jira_get_all_projects(self) -> List[Dict[str, Any]]:
        """Get all Jira projects"""
        result = await self.send_mcp_request("jira_get_all_projects", {})
        return result.get("projects", [])
    
    # Utility Methods
    async def get_available_tools(self) -> List[str]:
        """Get list of available MCP tools"""
        try:
            result = await self.send_mcp_request("tools/list", {})
            return [tool["name"] for tool in result.get("tools", [])]
        except Exception as e:
            self.logger.warning(f"Failed to get available tools: {str(e)}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Atlassian connection"""
        try:
            # Try to list available tools as a basic connectivity test
            tools = await self.get_available_tools()
            return {
                "status": "healthy",
                "server_running": self.running,
                "available_tools": len(tools),
                "tools": tools
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "server_running": self.running,
                "error": str(e)
            }
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start_server()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop_server()