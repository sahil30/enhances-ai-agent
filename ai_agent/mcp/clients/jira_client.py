"""
JIRA MCP Client

Specialized MCP client for interacting with JIRA issues and project management data.
Provides methods for searching issues, retrieving details, and managing JIRA-specific operations.
"""

import asyncio
from typing import Dict, List, Any, Optional
import structlog

from ..base.mcp_base import MCPClient, MCPConnectionConfig, MCPRequestError
from ..base.utils import (
    format_mcp_response, validate_mcp_params, sanitize_query,
    format_jira_result, build_jql_query, calculate_relevance_score
)

logger = structlog.get_logger(__name__)


class JiraMCPClient(MCPClient):
    """MCP client for JIRA server operations"""
    
    def __init__(self, config):
        """
        Initialize JIRA MCP client
        
        Args:
            config: Config object with JIRA configuration
        """
        mcp_config = MCPConnectionConfig(
            server_url=config.jira_mcp_server_url,
            access_token=config.jira_access_token,
            timeout=getattr(config, 'jira_timeout', 30.0),
            max_retries=getattr(config, 'jira_max_retries', 3)
        )
        
        super().__init__(mcp_config)
        
        self.base_url = config.jira_base_url
        self.default_fields = getattr(config, 'jira_fields', [
            'summary', 'description', 'status', 'assignee', 'reporter', 
            'priority', 'created', 'updated', 'resolutiondate', 'project',
            'issuetype', 'labels', 'components', 'fixVersions'
        ])
        self.project_filters = getattr(config, 'jira_projects', [])  # Optional project filtering
        
        self.logger = structlog.get_logger("mcp.jira")
    
    async def search_issues(self, jql: str, limit: int = 10, **options) -> List[Dict[str, Any]]:
        """
        Search JIRA issues using JQL (JIRA Query Language)
        
        Args:
            jql: JQL query string
            limit: Maximum number of results to return
            **options: Additional search options:
                - fields: List of fields to return
                - expand: List of fields to expand
                - validate_query: Whether to validate JQL syntax
        
        Returns:
            List of formatted JIRA issue results
        """
        try:
            if not jql or not isinstance(jql, str):
                self.logger.warning("Empty or invalid JQL query provided")
                return []
            
            # Build search parameters
            params = {
                "jql": jql.strip(),
                "maxResults": min(limit, 100),  # Cap at 100 results
                "fields": options.get('fields', self.default_fields),
                "expand": options.get('expand', ['changelog', 'renderedFields']),
                "validateQuery": options.get('validate_query', True)
            }
            
            # Validate parameters
            if not validate_mcp_params(params, ['jql'], ['maxResults', 'fields', 'expand', 'validateQuery']):
                return []
            
            self.logger.info(
                f"Searching JIRA issues",
                jql=jql,
                limit=limit
            )
            
            response = await self.send_request("jira.search", params)
            
            if "error" in response:
                self.logger.error(f"JIRA search failed: {response['error']}")
                return []
            
            result_data = response.get("result", {})
            issues = result_data.get("issues", [])
            
            # Format and enhance results
            formatted_results = []
            for issue in issues:
                try:
                    formatted_result = format_jira_result(issue, self.base_url)
                    
                    # Add search metadata
                    formatted_result['search_metadata'] = {
                        'jql': jql,
                        'total_results': result_data.get('total', 0),
                        'matched_fields': self._identify_matched_fields(issue, options.get('original_query', ''))
                    }
                    
                    # Calculate relevance score if original text query is provided
                    if options.get('original_query'):
                        formatted_result['relevance_score'] = calculate_relevance_score(
                            formatted_result, 
                            options['original_query']
                        )
                    
                    formatted_results.append(formatted_result)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to format JIRA result: {e}")
                    continue
            
            # Sort by relevance score if available, otherwise by updated date
            if any('relevance_score' in result for result in formatted_results):
                formatted_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            self.logger.info(
                f"JIRA search completed",
                results_count=len(formatted_results),
                total_available=result_data.get('total', 0)
            )
            
            return formatted_results[:limit]  # Apply final limit
            
        except MCPRequestError as e:
            self.logger.error(f"MCP request failed during JIRA search: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error during JIRA search: {e}")
            return []
    
    async def search_by_text(self, query: str, limit: int = 10, **filters) -> List[Dict[str, Any]]:
        """
        Search JIRA issues by text in summary or description
        
        Args:
            query: Text query to search for
            limit: Maximum number of results
            **filters: Additional filters:
                - project: Project key or list of project keys
                - status: Status name or list of statuses
                - assignee: Assignee username
                - priority: Priority name
                - issue_type: Issue type name
                - created_after: Date string (YYYY-MM-DD)
                - updated_after: Date string (YYYY-MM-DD)
        
        Returns:
            List of JIRA issues matching the text query
        """
        try:
            sanitized_query = sanitize_query(query)
            if not sanitized_query:
                return []
            
            # Build JQL query from text and filters
            jql = build_jql_query(sanitized_query, filters)
            
            # Add project filters if configured
            if self.project_filters and not filters.get('project'):
                project_conditions = [f'project = "{proj}"' for proj in self.project_filters]
                jql += f' AND ({" OR ".join(project_conditions)})'
            
            # Pass original query for relevance scoring
            options = {'original_query': sanitized_query}
            options.update(filters)
            
            return await self.search_issues(jql, limit, **options)
            
        except Exception as e:
            self.logger.error(f"Error in text search: {e}")
            return []
    
    async def get_issue_details(self, issue_key: str, expand_options: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get detailed information about a JIRA issue
        
        Args:
            issue_key: JIRA issue key (e.g., 'PROJ-123')
            expand_options: List of fields to expand
        
        Returns:
            Detailed issue information
        """
        try:
            if not issue_key or not isinstance(issue_key, str):
                self.logger.warning("Invalid issue key provided")
                return {}
            
            params = {
                "issueIdOrKey": issue_key.strip(),
                "fields": self.default_fields + ['attachment', 'comment', 'worklog'],
                "expand": expand_options or [
                    'changelog', 'comments', 'attachments', 'worklog',
                    'renderedFields', 'transitions', 'operations'
                ]
            }
            
            self.logger.info(f"Retrieving JIRA issue details", issue_key=issue_key)
            
            response = await self.send_request("jira.get_issue", params)
            
            if "error" in response:
                self.logger.error(f"Failed to get issue details: {response['error']}")
                return {}
            
            result = response.get("result", {})
            if not result:
                return {}
            
            # Format the detailed result
            detailed_result = format_jira_result(result, self.base_url)
            
            # Add extended information
            fields = result.get("fields", {})
            detailed_result.update({
                'extended_info': {
                    'environment': fields.get('environment', ''),
                    'security_level': fields.get('security', {}).get('name', '') if fields.get('security') else '',
                    'votes': fields.get('votes', {}).get('votes', 0),
                    'watchers': fields.get('watches', {}).get('watchCount', 0),
                    'time_tracking': {
                        'original_estimate': fields.get('timeoriginalestimate'),
                        'remaining_estimate': fields.get('timeestimate'),
                        'time_spent': fields.get('timespent')
                    }
                },
                'comments': [
                    {
                        'id': comment.get('id'),
                        'author': comment.get('author', {}).get('displayName', ''),
                        'body': comment.get('body', ''),
                        'created': comment.get('created', ''),
                        'updated': comment.get('updated', '')
                    }
                    for comment in result.get('fields', {}).get('comment', {}).get('comments', [])
                ],
                'attachments': [
                    {
                        'id': attachment.get('id'),
                        'filename': attachment.get('filename', ''),
                        'size': attachment.get('size', 0),
                        'content_type': attachment.get('mimeType', ''),
                        'created': attachment.get('created', ''),
                        'author': attachment.get('author', {}).get('displayName', '')
                    }
                    for attachment in fields.get('attachment', [])
                ],
                'changelog': self._format_changelog(result.get('changelog', {})),
                'transitions': [
                    {
                        'id': trans.get('id'),
                        'name': trans.get('name'),
                        'to_status': trans.get('to', {}).get('name', '')
                    }
                    for trans in result.get('transitions', [])
                ]
            })
            
            self.logger.info(f"Successfully retrieved issue details", issue_key=issue_key)
            return detailed_result
            
        except MCPRequestError as e:
            self.logger.error(f"MCP request failed during issue retrieval: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"Unexpected error during issue retrieval: {e}")
            return {}
    
    async def get_project_issues(self, project_key: str, limit: int = 50, **filters) -> List[Dict[str, Any]]:
        """
        Get all issues from a specific JIRA project
        
        Args:
            project_key: JIRA project key
            limit: Maximum number of issues to return
            **filters: Additional filters (status, assignee, etc.)
        
        Returns:
            List of issues in the project
        """
        try:
            # Add project filter to existing filters
            filters['project'] = project_key
            
            # Build JQL for project
            jql_parts = [f'project = "{project_key}"']
            
            if filters.get('status'):
                if isinstance(filters['status'], list):
                    status_list = ', '.join(f'"{s}"' for s in filters['status'])
                    jql_parts.append(f'status in ({status_list})')
                else:
                    jql_parts.append(f'status = "{filters["status"]}"')
            
            if filters.get('assignee'):
                jql_parts.append(f'assignee = "{filters["assignee"]}"')
            
            jql = ' AND '.join(jql_parts) + ' ORDER BY created DESC'
            
            return await self.search_issues(jql, limit)
            
        except Exception as e:
            self.logger.error(f"Error getting project issues: {e}")
            return []
    
    async def search_by_component(self, component_name: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search JIRA issues by component
        
        Args:
            component_name: Component name to search for
            limit: Maximum number of results
        
        Returns:
            List of issues with the specified component
        """
        try:
            jql = f'component = "{sanitize_query(component_name)}" ORDER BY updated DESC'
            return await self.search_issues(jql, limit)
            
        except Exception as e:
            self.logger.error(f"Error searching by component: {e}")
            return []
    
    async def get_user_issues(self, username: str, limit: int = 30) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get issues assigned to or reported by a specific user
        
        Args:
            username: JIRA username
            limit: Maximum number of issues per category
        
        Returns:
            Dictionary with 'assigned' and 'reported' issue lists
        """
        try:
            results = {'assigned': [], 'reported': []}
            
            # Get assigned issues
            assigned_jql = f'assignee = "{username}" ORDER BY updated DESC'
            results['assigned'] = await self.search_issues(assigned_jql, limit)
            
            # Get reported issues
            reported_jql = f'reporter = "{username}" ORDER BY created DESC'
            results['reported'] = await self.search_issues(reported_jql, limit)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error getting user issues: {e}")
            return {'assigned': [], 'reported': []}
    
    def _format_changelog(self, changelog: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format issue changelog entries"""
        if not changelog or 'histories' not in changelog:
            return []
        
        formatted_entries = []
        for history in changelog.get('histories', []):
            entry = {
                'id': history.get('id'),
                'author': history.get('author', {}).get('displayName', ''),
                'created': history.get('created', ''),
                'items': []
            }
            
            for item in history.get('items', []):
                entry['items'].append({
                    'field': item.get('field', ''),
                    'field_type': item.get('fieldtype', ''),
                    'from_value': item.get('fromString', ''),
                    'to_value': item.get('toString', '')
                })
            
            formatted_entries.append(entry)
        
        return formatted_entries
    
    def _identify_matched_fields(self, issue: Dict[str, Any], query: str) -> List[str]:
        """Identify which fields matched the search query"""
        if not query:
            return []
        
        matched_fields = []
        query_lower = query.lower()
        fields = issue.get('fields', {})
        
        # Check summary
        if query_lower in fields.get('summary', '').lower():
            matched_fields.append('summary')
        
        # Check description
        description = fields.get('description', '') or ''
        if query_lower in description.lower():
            matched_fields.append('description')
        
        # Check comments
        comments = fields.get('comment', {}).get('comments', [])
        if any(query_lower in comment.get('body', '').lower() for comment in comments):
            matched_fields.append('comments')
        
        # Check labels
        labels = fields.get('labels', [])
        if any(query_lower in label.lower() for label in labels):
            matched_fields.append('labels')
        
        # Check components
        components = [comp.get('name', '') for comp in fields.get('components', [])]
        if any(query_lower in comp.lower() for comp in components):
            matched_fields.append('components')
        
        return matched_fields