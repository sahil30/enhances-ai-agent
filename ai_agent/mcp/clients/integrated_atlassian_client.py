"""
Integrated Atlassian Client

Direct integration with mcp_atlassian library without Docker containers.
This client uses the mcp_atlassian source code directly for better performance
and easier deployment.
"""

import asyncio
import os
import sys
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import structlog

# Add mcp_atlassian to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from mcp_atlassian.confluence.client import ConfluenceClient
    from mcp_atlassian.jira.client import JiraClient
    from mcp_atlassian.utils.env import get_env_value, is_env_truthy
    from mcp_atlassian.models.base_models import ServerConfig
    from mcp_atlassian.exceptions import MCPAtlassianError
except ImportError as e:
    # Fallback for when mcp_atlassian is not available
    print(f"Warning: Could not import mcp_atlassian modules: {e}")
    ConfluenceClient = None
    JiraClient = None

from ..base.mcp_base import MCPConnectionError, MCPRequestError

logger = structlog.get_logger(__name__)


@dataclass
class IntegratedAtlassianConfig:
    """Configuration for integrated Atlassian client"""
    
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
    read_only_mode: bool = False
    enabled_tools: Optional[str] = None
    mcp_verbose: bool = False
    
    # Proxy settings
    http_proxy: Optional[str] = None
    https_proxy: Optional[str] = None
    no_proxy: Optional[str] = None


class IntegratedAtlassianClient:
    """
    Integrated Atlassian Client for direct mcp_atlassian integration
    
    This client uses the mcp_atlassian library directly instead of Docker containers
    for better performance and easier deployment.
    """
    
    def __init__(self, config: IntegratedAtlassianConfig):
        self.config = config
        self.confluence_client = None
        self.jira_client = None
        self.logger = structlog.get_logger("mcp.integrated_atlassian")
        
        # Set up environment variables for mcp_atlassian
        self._setup_environment()
        
    def _setup_environment(self):
        """Set up environment variables from configuration"""
        env_mapping = {
            # Confluence
            'CONFLUENCE_URL': self.config.confluence_url,
            'CONFLUENCE_USERNAME': self.config.confluence_username,
            'CONFLUENCE_API_TOKEN': self.config.confluence_api_token,
            'CONFLUENCE_PERSONAL_TOKEN': self.config.confluence_personal_token,
            'CONFLUENCE_SSL_VERIFY': str(self.config.confluence_ssl_verify).lower(),
            'CONFLUENCE_SPACES_FILTER': self.config.confluence_spaces_filter,
            'CONFLUENCE_CUSTOM_HEADERS': self.config.confluence_custom_headers,
            
            # Jira
            'JIRA_URL': self.config.jira_url,
            'JIRA_USERNAME': self.config.jira_username,
            'JIRA_API_TOKEN': self.config.jira_api_token,
            'JIRA_PERSONAL_TOKEN': self.config.jira_personal_token,
            'JIRA_SSL_VERIFY': str(self.config.jira_ssl_verify).lower(),
            'JIRA_PROJECTS_FILTER': self.config.jira_projects_filter,
            'JIRA_CUSTOM_HEADERS': self.config.jira_custom_headers,
            
            # OAuth
            'ATLASSIAN_OAUTH_CLOUD_ID': self.config.oauth_cloud_id,
            'ATLASSIAN_OAUTH_CLIENT_ID': self.config.oauth_client_id,
            'ATLASSIAN_OAUTH_CLIENT_SECRET': self.config.oauth_client_secret,
            'ATLASSIAN_OAUTH_REDIRECT_URI': self.config.oauth_redirect_uri,
            'ATLASSIAN_OAUTH_SCOPE': self.config.oauth_scope,
            'ATLASSIAN_OAUTH_ACCESS_TOKEN': self.config.oauth_access_token,
            
            # Server settings
            'READ_ONLY_MODE': str(self.config.read_only_mode).lower(),
            'ENABLED_TOOLS': self.config.enabled_tools,
            'MCP_VERBOSE': str(self.config.mcp_verbose).lower(),
            
            # Proxy
            'HTTP_PROXY': self.config.http_proxy,
            'HTTPS_PROXY': self.config.https_proxy,
            'NO_PROXY': self.config.no_proxy,
        }
        
        # Set environment variables (only if not None)
        for key, value in env_mapping.items():
            if value is not None:
                os.environ[key] = str(value)
    
    async def initialize(self) -> bool:
        """Initialize the Confluence and Jira clients"""
        try:
            if ConfluenceClient is None or JiraClient is None:
                raise MCPConnectionError("mcp_atlassian modules not available")
            
            # Initialize Confluence client if configured
            if self.config.confluence_url:
                self.confluence_client = ConfluenceClient()
                self.logger.info("Confluence client initialized")
            
            # Initialize Jira client if configured  
            if self.config.jira_url:
                self.jira_client = JiraClient()
                self.logger.info("Jira client initialized")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize clients: {str(e)}")
            raise MCPConnectionError(f"Failed to initialize clients: {str(e)}")
    
    # Confluence Methods
    async def confluence_search(self, query: str, space_keys: Optional[List[str]] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Search Confluence content"""
        if not self.confluence_client:
            raise MCPRequestError("Confluence client not initialized")
        
        try:
            # Build CQL query
            cql = query
            if space_keys:
                space_filter = " OR ".join([f'space.key = "{key}"' for key in space_keys])
                cql = f"({query}) AND ({space_filter})"
            
            # Use the confluence client search method
            results = await self.confluence_client.search_content(cql, limit=limit)
            return results.get('results', [])
            
        except Exception as e:
            self.logger.error(f"Confluence search failed: {str(e)}")
            raise MCPRequestError(f"Confluence search failed: {str(e)}")
    
    async def confluence_get_page(self, page_id: str, expand: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get Confluence page content"""
        if not self.confluence_client:
            raise MCPRequestError("Confluence client not initialized")
        
        try:
            expand_params = expand or ['body.storage', 'version']
            result = await self.confluence_client.get_page_by_id(page_id, expand=expand_params)
            return result
            
        except Exception as e:
            self.logger.error(f"Get Confluence page failed: {str(e)}")
            raise MCPRequestError(f"Get Confluence page failed: {str(e)}")
    
    async def confluence_create_page(self, space_key: str, title: str, content: str, 
                                   parent_id: Optional[str] = None) -> Dict[str, Any]:
        """Create new Confluence page"""
        if not self.confluence_client:
            raise MCPRequestError("Confluence client not initialized")
        
        if self.config.read_only_mode:
            raise MCPRequestError("Write operations disabled in read-only mode")
        
        try:
            page_data = {
                'type': 'page',
                'title': title,
                'space': {'key': space_key},
                'body': {
                    'storage': {
                        'value': content,
                        'representation': 'storage'
                    }
                }
            }
            
            if parent_id:
                page_data['ancestors'] = [{'id': parent_id}]
            
            result = await self.confluence_client.create_page(page_data)
            return result
            
        except Exception as e:
            self.logger.error(f"Create Confluence page failed: {str(e)}")
            raise MCPRequestError(f"Create Confluence page failed: {str(e)}")
    
    async def confluence_update_page(self, page_id: str, title: str, content: str, 
                                   version_number: int) -> Dict[str, Any]:
        """Update existing Confluence page"""
        if not self.confluence_client:
            raise MCPRequestError("Confluence client not initialized")
        
        if self.config.read_only_mode:
            raise MCPRequestError("Write operations disabled in read-only mode")
        
        try:
            page_data = {
                'id': page_id,
                'type': 'page',
                'title': title,
                'body': {
                    'storage': {
                        'value': content,
                        'representation': 'storage'
                    }
                },
                'version': {
                    'number': version_number + 1
                }
            }
            
            result = await self.confluence_client.update_page(page_data)
            return result
            
        except Exception as e:
            self.logger.error(f"Update Confluence page failed: {str(e)}")
            raise MCPRequestError(f"Update Confluence page failed: {str(e)}")
    
    # Jira Methods
    async def jira_search(self, jql: str, fields: Optional[List[str]] = None, 
                         max_results: int = 50) -> List[Dict[str, Any]]:
        """Search Jira issues using JQL"""
        if not self.jira_client:
            raise MCPRequestError("Jira client not initialized")
        
        try:
            search_params = {
                'jql': jql,
                'maxResults': max_results,
                'fields': fields or ['summary', 'status', 'assignee', 'created', 'updated']
            }
            
            result = await self.jira_client.search_issues(search_params)
            return result.get('issues', [])
            
        except Exception as e:
            self.logger.error(f"Jira search failed: {str(e)}")
            raise MCPRequestError(f"Jira search failed: {str(e)}")
    
    async def jira_get_issue(self, issue_key: str, expand: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get Jira issue details"""
        if not self.jira_client:
            raise MCPRequestError("Jira client not initialized")
        
        try:
            expand_params = expand or ['changelog', 'comments']
            result = await self.jira_client.get_issue(issue_key, expand=expand_params)
            return result
            
        except Exception as e:
            self.logger.error(f"Get Jira issue failed: {str(e)}")
            raise MCPRequestError(f"Get Jira issue failed: {str(e)}")
    
    async def jira_create_issue(self, project_key: str, summary: str, description: str,
                               issue_type: str = "Task", **kwargs) -> Dict[str, Any]:
        """Create new Jira issue"""
        if not self.jira_client:
            raise MCPRequestError("Jira client not initialized")
        
        if self.config.read_only_mode:
            raise MCPRequestError("Write operations disabled in read-only mode")
        
        try:
            issue_data = {
                'fields': {
                    'project': {'key': project_key},
                    'summary': summary,
                    'description': description,
                    'issuetype': {'name': issue_type},
                    **kwargs
                }
            }
            
            result = await self.jira_client.create_issue(issue_data)
            return result
            
        except Exception as e:
            self.logger.error(f"Create Jira issue failed: {str(e)}")
            raise MCPRequestError(f"Create Jira issue failed: {str(e)}")
    
    async def jira_update_issue(self, issue_key: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing Jira issue"""
        if not self.jira_client:
            raise MCPRequestError("Jira client not initialized")
        
        if self.config.read_only_mode:
            raise MCPRequestError("Write operations disabled in read-only mode")
        
        try:
            update_data = {'fields': fields}
            result = await self.jira_client.update_issue(issue_key, update_data)
            return result or {'success': True}
            
        except Exception as e:
            self.logger.error(f"Update Jira issue failed: {str(e)}")
            raise MCPRequestError(f"Update Jira issue failed: {str(e)}")
    
    async def jira_add_comment(self, issue_key: str, comment: str) -> Dict[str, Any]:
        """Add comment to Jira issue"""
        if not self.jira_client:
            raise MCPRequestError("Jira client not initialized")
        
        if self.config.read_only_mode:
            raise MCPRequestError("Write operations disabled in read-only mode")
        
        try:
            comment_data = {
                'body': comment
            }
            
            result = await self.jira_client.add_comment(issue_key, comment_data)
            return result
            
        except Exception as e:
            self.logger.error(f"Add Jira comment failed: {str(e)}")
            raise MCPRequestError(f"Add Jira comment failed: {str(e)}")
    
    async def jira_transition_issue(self, issue_key: str, transition_name: str,
                                   comment: Optional[str] = None) -> Dict[str, Any]:
        """Transition Jira issue to new status"""
        if not self.jira_client:
            raise MCPRequestError("Jira client not initialized")
        
        if self.config.read_only_mode:
            raise MCPRequestError("Write operations disabled in read-only mode")
        
        try:
            # Get available transitions
            transitions = await self.jira_client.get_issue_transitions(issue_key)
            
            # Find the transition by name
            transition_id = None
            for transition in transitions.get('transitions', []):
                if transition['name'].lower() == transition_name.lower():
                    transition_id = transition['id']
                    break
            
            if not transition_id:
                raise MCPRequestError(f"Transition '{transition_name}' not found")
            
            # Perform transition
            transition_data = {
                'transition': {'id': transition_id}
            }
            
            if comment:
                transition_data['update'] = {
                    'comment': [{'add': {'body': comment}}]
                }
            
            result = await self.jira_client.transition_issue(issue_key, transition_data)
            return result or {'success': True}
            
        except Exception as e:
            self.logger.error(f"Transition Jira issue failed: {str(e)}")
            raise MCPRequestError(f"Transition Jira issue failed: {str(e)}")
    
    async def jira_get_all_projects(self) -> List[Dict[str, Any]]:
        """Get all Jira projects"""
        if not self.jira_client:
            raise MCPRequestError("Jira client not initialized")
        
        try:
            result = await self.jira_client.get_all_projects()
            return result
            
        except Exception as e:
            self.logger.error(f"Get Jira projects failed: {str(e)}")
            raise MCPRequestError(f"Get Jira projects failed: {str(e)}")
    
    # Utility Methods
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Atlassian connections"""
        health_status = {
            "status": "healthy",
            "confluence": {"available": False, "error": None},
            "jira": {"available": False, "error": None}
        }
        
        # Check Confluence
        if self.confluence_client:
            try:
                # Try a simple search
                await self.confluence_search("type=page", limit=1)
                health_status["confluence"]["available"] = True
            except Exception as e:
                health_status["confluence"]["error"] = str(e)
                health_status["status"] = "degraded"
        
        # Check Jira  
        if self.jira_client:
            try:
                # Try getting projects
                await self.jira_get_all_projects()
                health_status["jira"]["available"] = True
            except Exception as e:
                health_status["jira"]["error"] = str(e)
                health_status["status"] = "degraded"
        
        # Overall status
        if not health_status["confluence"]["available"] and not health_status["jira"]["available"]:
            health_status["status"] = "unhealthy"
        
        return health_status
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        # Clean up if needed
        pass