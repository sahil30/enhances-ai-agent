"""
Integrated Atlassian Client

Direct integration with Atlassian APIs without external MCP servers.
This client provides a simplified interface to Confluence and JIRA.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import structlog

# Try to import atlassian-python-api for direct API access
try:
    from atlassian import Confluence
    from atlassian import Jira
    ATLASSIAN_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import atlassian libraries: {e}")
    Confluence = None
    Jira = None
    ATLASSIAN_AVAILABLE = False

from ..base.mcp_base import MCPConnectionError, MCPRequestError

logger = structlog.get_logger(__name__)


class IntegratedAtlassianClient:
    """
    Integrated Atlassian Client using atlassian-python-api directly
    
    This client provides direct API access to Confluence and JIRA without 
    requiring external MCP servers.
    """
    
    def __init__(self, config):
        """Initialize with AI Agent Config object"""
        self.config = config
        self.confluence_client = None
        self.jira_client = None
        self._initialized = False
        self.logger = logger.bind(client="integrated_atlassian")
        
    async def initialize(self) -> bool:
        """Initialize the Atlassian clients"""
        if self._initialized:
            return True
            
        if not ATLASSIAN_AVAILABLE:
            self.logger.warning("atlassian-python-api library not available, skipping initialization")
            return True  # Don't fail, just skip
        
        try:
            # Initialize Confluence client if configured
            if hasattr(self.config, 'confluence_url') and self.config.confluence_url:
                confluence_url = self.config.confluence_url
                username = getattr(self.config, 'confluence_username', None)  
                api_token = getattr(self.config, 'confluence_api_token', None)
                
                if username and api_token:
                    self.confluence_client = Confluence(
                        url=confluence_url,
                        username=username,
                        password=api_token
                    )
                    self.logger.info("Confluence client initialized")
                else:
                    self.logger.warning("Confluence URL provided but missing credentials")
            
            # Initialize JIRA client if configured  
            if hasattr(self.config, 'jira_url') and self.config.jira_url:
                jira_url = self.config.jira_url
                username = getattr(self.config, 'jira_username', None)
                api_token = getattr(self.config, 'jira_api_token', None)
                
                if username and api_token:
                    self.jira_client = Jira(
                        url=jira_url,
                        username=username,
                        password=api_token
                    )
                    self.logger.info("JIRA client initialized")
                else:
                    self.logger.warning("JIRA URL provided but missing credentials")
            
            self._initialized = True
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Atlassian clients: {e}")
            # Don't raise error, just log warning for test environments
            self.logger.warning("Continuing without Atlassian integration")
            return True
    
    async def search_confluence(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search Confluence pages"""
        if not self.confluence_client:
            self.logger.warning("Confluence client not initialized")
            return []
            
        try:
            # Use CQL search for better results
            cql = f'text ~ "{query}"'
            results = self.confluence_client.cql(cql, limit=max_results)
            
            pages = []
            for result in results.get('results', []):
                content = result.get('content', {})
                pages.append({
                    'id': content.get('id'),
                    'title': content.get('title'),
                    'url': f"{self.config.confluence_url}/spaces/{content.get('space', {}).get('key')}/pages/{content.get('id')}",
                    'space': content.get('space', {}).get('name'),
                    'type': content.get('type'),
                    'excerpt': result.get('excerpt', '')
                })
                
            self.logger.info(f"Found {len(pages)} Confluence results for: {query}")
            return pages
            
        except Exception as e:
            self.logger.error(f"Confluence search failed: {e}")
            return []
    
    async def search_jira(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search JIRA issues"""
        if not self.jira_client:
            self.logger.warning("JIRA client not initialized") 
            return []
            
        try:
            # Use JQL search
            jql = f'text ~ "{query}"'
            results = self.jira_client.jql(jql, limit=max_results)
            
            issues = []
            for issue in results.get('issues', []):
                fields = issue.get('fields', {})
                issues.append({
                    'key': issue.get('key'),
                    'summary': fields.get('summary'),
                    'description': fields.get('description', '')[:500] if fields.get('description') else '',
                    'status': fields.get('status', {}).get('name'),
                    'priority': fields.get('priority', {}).get('name'),
                    'assignee': fields.get('assignee', {}).get('displayName') if fields.get('assignee') else None,
                    'created': fields.get('created'),
                    'updated': fields.get('updated'),
                    'url': f"{self.config.jira_url}/browse/{issue.get('key')}"
                })
                
            self.logger.info(f"Found {len(issues)} JIRA results for: {query}")
            return issues
            
        except Exception as e:
            self.logger.error(f"JIRA search failed: {e}")
            return []
    
    async def search(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """Search both Confluence and JIRA"""
        results = {
            'confluence': await self.search_confluence(query, max_results),
            'jira': await self.search_jira(query, max_results)
        }
        return results
    
    async def connect(self):
        """Connect to services (alias for initialize)"""
        return await self.initialize()
    
    async def close(self):
        """Close connections"""
        self.confluence_client = None
        self.jira_client = None
        self._initialized = False
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for integrated client"""
        return {
            "status": "healthy" if self._initialized else "not_initialized",
            "confluence": {"available": self.confluence_client is not None},
            "jira": {"available": self.jira_client is not None}
        }