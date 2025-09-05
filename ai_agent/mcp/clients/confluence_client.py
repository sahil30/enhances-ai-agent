"""
Confluence MCP Client

Specialized MCP client for interacting with Confluence documentation and wiki content.
Provides methods for searching pages, retrieving content, and managing Confluence-specific operations.
"""

import asyncio
from typing import Dict, List, Any, Optional
import structlog

from ..base.mcp_base import MCPClient, MCPConnectionConfig, MCPRequestError
from ..base.utils import (
    format_mcp_response, validate_mcp_params, sanitize_query,
    format_confluence_result, calculate_relevance_score
)

logger = structlog.get_logger(__name__)


class ConfluenceMCPClient(MCPClient):
    """MCP client for Confluence server operations"""
    
    def __init__(self, config):
        """
        Initialize Confluence MCP client
        
        Args:
            config: Config object with Confluence configuration
        """
        mcp_config = MCPConnectionConfig(
            server_url=config.confluence_mcp_server_url,
            access_token=config.confluence_access_token,
            timeout=getattr(config, 'confluence_timeout', 30.0),
            max_retries=getattr(config, 'confluence_max_retries', 3)
        )
        
        super().__init__(mcp_config)
        
        self.base_url = config.confluence_base_url
        self.space_filters = getattr(config, 'confluence_spaces', [])  # Optional space filtering
        self.content_types = getattr(config, 'confluence_content_types', ['page', 'blogpost'])
        
        self.logger = structlog.get_logger("mcp.confluence")
    
    async def search_pages(self, query: str, limit: int = 10, **options) -> List[Dict[str, Any]]:
        """
        Search Confluence pages and blog posts
        
        Args:
            query: Search query text
            limit: Maximum number of results to return
            **options: Additional search options:
                - spaces: List of space keys to search in
                - content_types: Types of content to search ('page', 'blogpost', etc.)
                - expand: List of fields to expand in results
                - sort: Sort order ('relevance', 'title', 'modified')
        
        Returns:
            List of formatted Confluence page/post results
        """
        try:
            sanitized_query = sanitize_query(query)
            if not sanitized_query:
                self.logger.warning("Empty or invalid search query provided")
                return []
            
            # Build search parameters
            params = {
                "cql": self._build_cql_query(sanitized_query, options),
                "limit": min(limit, 100),  # Cap at 100 results
                "expand": options.get('expand', [
                    'body.view', 'body.storage', 'version', 'space', 
                    'metadata.labels', 'history.lastUpdated'
                ])
            }
            
            # Validate parameters
            if not validate_mcp_params(params, ['cql'], ['limit', 'expand']):
                return []
            
            self.logger.info(
                f"Searching Confluence pages",
                query=sanitized_query,
                limit=limit,
                cql=params['cql']
            )
            
            response = await self.send_request("confluence.search", params)
            
            if "error" in response:
                self.logger.error(f"Confluence search failed: {response['error']}")
                return []
            
            results = response.get("result", {}).get("results", [])
            
            # Format and enhance results
            formatted_results = []
            for result in results:
                try:
                    formatted_result = format_confluence_result(result, self.base_url)
                    
                    # Calculate relevance score
                    formatted_result['relevance_score'] = calculate_relevance_score(formatted_result, query)
                    
                    # Add search metadata
                    formatted_result['search_metadata'] = {
                        'query': query,
                        'matched_fields': self._identify_matched_fields(result, sanitized_query),
                        'content_type': formatted_result.get('type', 'page')
                    }
                    
                    formatted_results.append(formatted_result)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to format Confluence result: {e}")
                    continue
            
            # Sort by relevance score
            formatted_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            self.logger.info(
                f"Confluence search completed",
                results_count=len(formatted_results),
                query=sanitized_query
            )
            
            return formatted_results[:limit]  # Apply final limit
            
        except MCPRequestError as e:
            self.logger.error(f"MCP request failed during Confluence search: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error during Confluence search: {e}")
            return []
    
    async def get_page_content(self, page_id: str, expand_options: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get full content of a Confluence page
        
        Args:
            page_id: Confluence page ID
            expand_options: List of fields to expand
        
        Returns:
            Detailed page information with full content
        """
        try:
            if not page_id or not isinstance(page_id, str):
                self.logger.warning("Invalid page ID provided")
                return {}
            
            params = {
                "id": page_id,
                "expand": expand_options or [
                    'body.storage', 'body.view', 'version', 'space', 
                    'ancestors', 'children.page', 'metadata.labels',
                    'metadata.properties', 'history', 'restrictions'
                ]
            }
            
            self.logger.info(f"Retrieving Confluence page content", page_id=page_id)
            
            response = await self.send_request("confluence.get_content", params)
            
            if "error" in response:
                self.logger.error(f"Failed to get page content: {response['error']}")
                return {}
            
            result = response.get("result", {})
            if not result:
                return {}
            
            # Format the detailed result
            detailed_result = format_confluence_result(result, self.base_url)
            
            # Add extended information
            detailed_result.update({
                'full_content': {
                    'storage': result.get('body', {}).get('storage', {}).get('value', ''),
                    'view': result.get('body', {}).get('view', {}).get('value', ''),
                    'export_view': result.get('body', {}).get('export_view', {}).get('value', '')
                },
                'ancestors': [
                    {
                        'id': ancestor.get('id'),
                        'title': ancestor.get('title'),
                        'type': ancestor.get('type')
                    }
                    for ancestor in result.get('ancestors', [])
                ],
                'children': [
                    {
                        'id': child.get('id'),
                        'title': child.get('title'),
                        'type': child.get('type')
                    }
                    for child in result.get('children', {}).get('page', {}).get('results', [])
                ],
                'restrictions': result.get('restrictions', {}),
                'metadata': {
                    'properties': result.get('metadata', {}).get('properties', {}),
                    'frontend_url': result.get('_links', {}).get('base', '') + result.get('_links', {}).get('webui', '')
                }
            })
            
            self.logger.info(f"Successfully retrieved page content", page_id=page_id)
            return detailed_result
            
        except MCPRequestError as e:
            self.logger.error(f"MCP request failed during page retrieval: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"Unexpected error during page retrieval: {e}")
            return {}
    
    async def get_space_content(self, space_key: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all content from a specific Confluence space
        
        Args:
            space_key: Confluence space key
            limit: Maximum number of pages to return
        
        Returns:
            List of pages in the space
        """
        try:
            params = {
                "spaceKey": space_key,
                "limit": min(limit, 100),
                "expand": ['version', 'space', 'body.view']
            }
            
            self.logger.info(f"Getting space content", space_key=space_key)
            
            response = await self.send_request("confluence.get_space_content", params)
            
            if "error" in response:
                return []
            
            results = response.get("result", {}).get("results", [])
            
            formatted_results = []
            for result in results:
                formatted_result = format_confluence_result(result, self.base_url)
                formatted_results.append(formatted_result)
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Error getting space content: {e}")
            return []
    
    async def search_by_label(self, label: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search Confluence content by label
        
        Args:
            label: Label name to search for
            limit: Maximum number of results
        
        Returns:
            List of pages/posts with the specified label
        """
        try:
            cql_query = f'label = "{sanitize_query(label)}"'
            
            params = {
                "cql": cql_query,
                "limit": limit,
                "expand": ['body.view', 'version', 'space', 'metadata.labels']
            }
            
            response = await self.send_request("confluence.search", params)
            
            if "error" in response:
                return []
            
            results = response.get("result", {}).get("results", [])
            
            formatted_results = []
            for result in results:
                formatted_result = format_confluence_result(result, self.base_url)
                formatted_results.append(formatted_result)
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Error searching by label: {e}")
            return []
    
    def _build_cql_query(self, query: str, options: Dict[str, Any]) -> str:
        """Build Confluence Query Language (CQL) query"""
        cql_parts = []
        
        # Add text search
        if query:
            # Search in title and text content
            cql_parts.append(f'(title ~ "{query}" OR text ~ "{query}")')
        
        # Add space filters
        spaces = options.get('spaces', self.space_filters)
        if spaces:
            space_conditions = [f'space = "{space}"' for space in spaces]
            cql_parts.append(f'({" OR ".join(space_conditions)})')
        
        # Add content type filters
        content_types = options.get('content_types', self.content_types)
        if content_types and len(content_types) < 10:  # Don't add if too many types
            type_conditions = [f'type = "{ctype}"' for ctype in content_types]
            cql_parts.append(f'({" OR ".join(type_conditions)})')
        
        # Add date filters if provided
        if options.get('created_after'):
            cql_parts.append(f'created >= "{options["created_after"]}"')
        
        if options.get('modified_after'):
            cql_parts.append(f'lastModified >= "{options["modified_after"]}"')
        
        # Combine all parts
        cql_query = " AND ".join(cql_parts) if cql_parts else 'type = "page"'
        
        # Add sorting
        sort_option = options.get('sort', 'relevance')
        if sort_option == 'title':
            cql_query += " ORDER BY title ASC"
        elif sort_option == 'modified':
            cql_query += " ORDER BY lastModified DESC"
        elif sort_option == 'created':
            cql_query += " ORDER BY created DESC"
        # Default is relevance (no explicit ORDER BY needed)
        
        self.logger.debug(f"Built CQL query: {cql_query}")
        return cql_query
    
    def _identify_matched_fields(self, result: Dict[str, Any], query: str) -> List[str]:
        """Identify which fields matched the search query"""
        matched_fields = []
        query_lower = query.lower()
        
        # Check title
        if query_lower in result.get('title', '').lower():
            matched_fields.append('title')
        
        # Check content/excerpt
        content = result.get('excerpt', '') or result.get('body', {}).get('view', {}).get('value', '')
        if query_lower in content.lower():
            matched_fields.append('content')
        
        # Check space name
        if query_lower in result.get('space', {}).get('name', '').lower():
            matched_fields.append('space')
        
        # Check labels
        labels = [label.get('name', '').lower() for label in result.get('metadata', {}).get('labels', {}).get('results', [])]
        if any(query_lower in label for label in labels):
            matched_fields.append('labels')
        
        return matched_fields