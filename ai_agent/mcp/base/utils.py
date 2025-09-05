"""
MCP Utility Functions

Common utilities for MCP client operations including response formatting,
parameter validation, and data transformation helpers.
"""

import re
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


def format_mcp_response(response: Dict[str, Any], source_type: str = "unknown") -> Dict[str, Any]:
    """Format MCP response with standardized structure"""
    if not response or "result" not in response:
        return {}
    
    result = response["result"]
    
    # Add metadata about the response
    formatted = {
        "source_type": source_type,
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": response.get("id"),
        "data": result
    }
    
    return formatted


def validate_mcp_params(params: Dict[str, Any], required_fields: List[str], 
                       optional_fields: List[str] = None) -> bool:
    """Validate MCP request parameters"""
    if optional_fields is None:
        optional_fields = []
    
    # Check required fields
    missing_fields = []
    for field in required_fields:
        if field not in params or params[field] is None:
            missing_fields.append(field)
    
    if missing_fields:
        logger.error(f"Missing required MCP parameters: {missing_fields}")
        return False
    
    # Check for unknown fields
    all_allowed_fields = set(required_fields + optional_fields)
    unknown_fields = set(params.keys()) - all_allowed_fields
    
    if unknown_fields:
        logger.warning(f"Unknown MCP parameters (will be ignored): {unknown_fields}")
    
    return True


def sanitize_query(query: str, max_length: int = 1000) -> str:
    """Sanitize query string for MCP requests"""
    if not query or not isinstance(query, str):
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\';\\]', '', query.strip())
    
    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].strip()
        logger.warning(f"Query truncated to {max_length} characters")
    
    return sanitized


def format_confluence_result(result: Dict[str, Any], base_url: str = "") -> Dict[str, Any]:
    """Format Confluence search result into standardized structure"""
    try:
        formatted_result = {
            "id": result.get("id", ""),
            "title": result.get("title", "Untitled"),
            "type": result.get("type", "page"),
            "url": f"{base_url}{result.get('_links', {}).get('webui', '')}",
            "excerpt": clean_html(result.get("excerpt", "")),
            "space": {
                "key": result.get("space", {}).get("key", ""),
                "name": result.get("space", {}).get("name", "")
            },
            "version": {
                "number": result.get("version", {}).get("number", 1),
                "when": result.get("version", {}).get("when", ""),
                "by": result.get("version", {}).get("by", {}).get("displayName", "Unknown")
            },
            "content": clean_html(result.get("body", {}).get("view", {}).get("value", ""))[:2000],
            "labels": [label.get("name", "") for label in result.get("metadata", {}).get("labels", {}).get("results", [])],
            "created": result.get("history", {}).get("createdDate", ""),
            "modified": result.get("version", {}).get("when", "")
        }
        
        return formatted_result
        
    except Exception as e:
        logger.error(f"Error formatting Confluence result: {e}")
        return {
            "id": result.get("id", "unknown"),
            "title": result.get("title", "Error formatting result"),
            "error": str(e)
        }


def format_jira_result(result: Dict[str, Any], base_url: str = "") -> Dict[str, Any]:
    """Format JIRA search result into standardized structure"""
    try:
        fields = result.get("fields", {})
        
        formatted_result = {
            "key": result.get("key", ""),
            "id": result.get("id", ""),
            "summary": fields.get("summary", ""),
            "description": clean_html(fields.get("description", "")),
            "status": {
                "name": fields.get("status", {}).get("name", "Unknown"),
                "category": fields.get("status", {}).get("statusCategory", {}).get("name", "")
            },
            "priority": {
                "name": fields.get("priority", {}).get("name", "Unknown"),
                "id": fields.get("priority", {}).get("id", "")
            },
            "issue_type": {
                "name": fields.get("issuetype", {}).get("name", "Unknown"),
                "icon": fields.get("issuetype", {}).get("iconUrl", "")
            },
            "assignee": {
                "name": fields.get("assignee", {}).get("displayName", "Unassigned") if fields.get("assignee") else "Unassigned",
                "email": fields.get("assignee", {}).get("emailAddress", "") if fields.get("assignee") else ""
            },
            "reporter": {
                "name": fields.get("reporter", {}).get("displayName", "Unknown") if fields.get("reporter") else "Unknown",
                "email": fields.get("reporter", {}).get("emailAddress", "") if fields.get("reporter") else ""
            },
            "project": {
                "key": fields.get("project", {}).get("key", ""),
                "name": fields.get("project", {}).get("name", "")
            },
            "created": fields.get("created", ""),
            "updated": fields.get("updated", ""),
            "resolved": fields.get("resolutiondate", ""),
            "url": f"{base_url}/browse/{result.get('key', '')}",
            "labels": fields.get("labels", []),
            "components": [comp.get("name", "") for comp in fields.get("components", [])],
            "fix_versions": [version.get("name", "") for version in fields.get("fixVersions", [])]
        }
        
        return formatted_result
        
    except Exception as e:
        logger.error(f"Error formatting JIRA result: {e}")
        return {
            "key": result.get("key", "unknown"),
            "summary": "Error formatting result",
            "error": str(e)
        }


def clean_html(html_content: str) -> str:
    """Remove HTML tags and clean up content"""
    if not html_content or not isinstance(html_content, str):
        return ""
    
    # Remove HTML tags
    clean_text = re.sub(r'<[^>]+>', '', html_content)
    
    # Remove extra whitespace
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    # Decode common HTML entities
    html_entities = {
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&#39;': "'",
        '&nbsp;': ' '
    }
    
    for entity, char in html_entities.items():
        clean_text = clean_text.replace(entity, char)
    
    return clean_text


def build_jql_query(text_query: str, filters: Dict[str, Any] = None) -> str:
    """Build JQL query from text query and optional filters"""
    if filters is None:
        filters = {}
    
    # Start with text search
    jql_parts = [f'text ~ "{sanitize_query(text_query)}"']
    
    # Add filters
    if filters.get("project"):
        jql_parts.append(f'project = "{filters["project"]}"')
    
    if filters.get("status"):
        if isinstance(filters["status"], list):
            status_list = ', '.join(f'"{s}"' for s in filters["status"])
            jql_parts.append(f'status in ({status_list})')
        else:
            jql_parts.append(f'status = "{filters["status"]}"')
    
    if filters.get("assignee"):
        jql_parts.append(f'assignee = "{filters["assignee"]}"')
    
    if filters.get("priority"):
        jql_parts.append(f'priority = "{filters["priority"]}"')
    
    if filters.get("created_after"):
        jql_parts.append(f'created >= "{filters["created_after"]}"')
    
    if filters.get("updated_after"):
        jql_parts.append(f'updated >= "{filters["updated_after"]}"')
    
    # Add default ordering
    jql = " AND ".join(jql_parts) + " ORDER BY updated DESC"
    
    logger.debug(f"Built JQL query: {jql}")
    return jql


def extract_error_details(response: Dict[str, Any]) -> Dict[str, Any]:
    """Extract detailed error information from MCP response"""
    if "error" not in response:
        return {}
    
    error = response["error"]
    
    return {
        "code": error.get("code", -1),
        "message": error.get("message", "Unknown error"),
        "data": error.get("data", {}),
        "type": error.get("type", "MCPError"),
        "request_id": response.get("id")
    }


def calculate_relevance_score(result: Dict[str, Any], query: str) -> float:
    """Calculate relevance score for search results"""
    score = 0.0
    query_lower = query.lower()
    query_words = set(query_lower.split())
    
    # Title relevance (highest weight)
    title = result.get("title", "").lower()
    if query_lower in title:
        score += 0.4
    else:
        title_words = set(title.split())
        common_words = query_words.intersection(title_words)
        score += (len(common_words) / len(query_words)) * 0.3
    
    # Content relevance
    content = result.get("content", "").lower()
    if query_lower in content:
        score += 0.2
    else:
        content_words = set(content.split())
        common_words = query_words.intersection(content_words)
        score += (len(common_words) / len(query_words)) * 0.15
    
    # Excerpt/description relevance
    excerpt = result.get("excerpt", "").lower() or result.get("description", "").lower()
    if query_lower in excerpt:
        score += 0.15
    else:
        excerpt_words = set(excerpt.split())
        common_words = query_words.intersection(excerpt_words)
        score += (len(common_words) / len(query_words)) * 0.1
    
    # Recency bonus (for updated content)
    try:
        updated = result.get("updated") or result.get("modified")
        if updated:
            from datetime import datetime, timezone
            update_time = datetime.fromisoformat(updated.replace('Z', '+00:00'))
            days_old = (datetime.now(timezone.utc) - update_time).days
            recency_bonus = max(0, (30 - days_old) / 30 * 0.1)  # Bonus for content updated within 30 days
            score += recency_bonus
    except Exception:
        pass  # Skip recency bonus if date parsing fails
    
    return min(1.0, score)  # Cap at 1.0