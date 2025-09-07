"""
Atlassian MCP Configuration

This module provides easy configuration setup for the Atlassian MCP integration.
It includes configuration classes and helper functions for different deployment types.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from ai_agent.mcp import AtlassianConfig


@dataclass
class AtlassianCloudConfig:
    """Configuration for Atlassian Cloud deployment"""
    
    # Required
    confluence_url: str
    confluence_username: str
    confluence_api_token: str
    jira_url: str
    jira_username: str
    jira_api_token: str
    
    # Optional filters
    confluence_spaces_filter: Optional[str] = None
    jira_projects_filter: Optional[str] = None
    
    # Optional settings
    read_only_mode: bool = False
    enabled_tools: Optional[str] = None
    mcp_verbose: bool = False
    
    def to_atlassian_config(self) -> AtlassianConfig:
        """Convert to AtlassianConfig"""
        return AtlassianConfig(
            confluence_url=self.confluence_url,
            confluence_username=self.confluence_username,
            confluence_api_token=self.confluence_api_token,
            jira_url=self.jira_url,
            jira_username=self.jira_username,
            jira_api_token=self.jira_api_token,
            confluence_spaces_filter=self.confluence_spaces_filter,
            jira_projects_filter=self.jira_projects_filter,
            read_only_mode=self.read_only_mode,
            enabled_tools=self.enabled_tools,
            mcp_verbose=self.mcp_verbose,
            mcp_logging_stdout=True
        )


@dataclass 
class AtlassianServerConfig:
    """Configuration for Atlassian Server/Data Center deployment"""
    
    # Required
    confluence_url: str
    confluence_personal_token: str
    jira_url: str
    jira_personal_token: str
    
    # SSL settings
    confluence_ssl_verify: bool = True
    jira_ssl_verify: bool = True
    
    # Optional filters
    confluence_spaces_filter: Optional[str] = None
    jira_projects_filter: Optional[str] = None
    
    # Optional settings
    read_only_mode: bool = False
    enabled_tools: Optional[str] = None
    mcp_verbose: bool = False
    
    def to_atlassian_config(self) -> AtlassianConfig:
        """Convert to AtlassianConfig"""
        return AtlassianConfig(
            confluence_url=self.confluence_url,
            confluence_personal_token=self.confluence_personal_token,
            confluence_ssl_verify=self.confluence_ssl_verify,
            jira_url=self.jira_url,
            jira_personal_token=self.jira_personal_token,
            jira_ssl_verify=self.jira_ssl_verify,
            confluence_spaces_filter=self.confluence_spaces_filter,
            jira_projects_filter=self.jira_projects_filter,
            read_only_mode=self.read_only_mode,
            enabled_tools=self.enabled_tools,
            mcp_verbose=self.mcp_verbose,
            mcp_logging_stdout=True
        )


@dataclass
class AtlassianOAuthConfig:
    """Configuration for OAuth 2.0 authentication (Cloud only)"""
    
    # Required
    confluence_url: str
    jira_url: str
    oauth_cloud_id: str
    oauth_client_id: str
    oauth_client_secret: str
    oauth_redirect_uri: str
    oauth_scope: str
    
    # Optional pre-existing token (BYOT)
    oauth_access_token: Optional[str] = None
    
    # Optional settings
    read_only_mode: bool = False
    enabled_tools: Optional[str] = None
    mcp_verbose: bool = False
    
    def to_atlassian_config(self) -> AtlassianConfig:
        """Convert to AtlassianConfig"""
        return AtlassianConfig(
            confluence_url=self.confluence_url,
            jira_url=self.jira_url,
            oauth_cloud_id=self.oauth_cloud_id,
            oauth_client_id=self.oauth_client_id,
            oauth_client_secret=self.oauth_client_secret,
            oauth_redirect_uri=self.oauth_redirect_uri,
            oauth_scope=self.oauth_scope,
            oauth_access_token=self.oauth_access_token,
            read_only_mode=self.read_only_mode,
            enabled_tools=self.enabled_tools,
            mcp_verbose=self.mcp_verbose,
            mcp_logging_stdout=True
        )


def create_cloud_config_from_env() -> AtlassianCloudConfig:
    """Create Cloud configuration from environment variables"""
    
    required_vars = {
        "CONFLUENCE_URL": "confluence_url",
        "CONFLUENCE_USERNAME": "confluence_username", 
        "CONFLUENCE_API_TOKEN": "confluence_api_token",
        "JIRA_URL": "jira_url",
        "JIRA_USERNAME": "jira_username",
        "JIRA_API_TOKEN": "jira_api_token"
    }
    
    config_dict = {}
    for env_var, config_key in required_vars.items():
        value = os.getenv(env_var)
        if not value:
            raise ValueError(f"Required environment variable {env_var} is not set")
        config_dict[config_key] = value
    
    # Optional variables
    optional_vars = {
        "CONFLUENCE_SPACES_FILTER": "confluence_spaces_filter",
        "JIRA_PROJECTS_FILTER": "jira_projects_filter", 
        "READ_ONLY_MODE": "read_only_mode",
        "ENABLED_TOOLS": "enabled_tools",
        "MCP_VERBOSE": "mcp_verbose"
    }
    
    for env_var, config_key in optional_vars.items():
        value = os.getenv(env_var)
        if value:
            if config_key in ["read_only_mode", "mcp_verbose"]:
                config_dict[config_key] = value.lower() in ("true", "1", "yes")
            else:
                config_dict[config_key] = value
    
    return AtlassianCloudConfig(**config_dict)


def create_server_config_from_env() -> AtlassianServerConfig:
    """Create Server/Data Center configuration from environment variables"""
    
    required_vars = {
        "CONFLUENCE_URL": "confluence_url",
        "CONFLUENCE_PERSONAL_TOKEN": "confluence_personal_token",
        "JIRA_URL": "jira_url", 
        "JIRA_PERSONAL_TOKEN": "jira_personal_token"
    }
    
    config_dict = {}
    for env_var, config_key in required_vars.items():
        value = os.getenv(env_var)
        if not value:
            raise ValueError(f"Required environment variable {env_var} is not set")
        config_dict[config_key] = value
    
    # Optional variables
    optional_vars = {
        "CONFLUENCE_SSL_VERIFY": "confluence_ssl_verify",
        "JIRA_SSL_VERIFY": "jira_ssl_verify",
        "CONFLUENCE_SPACES_FILTER": "confluence_spaces_filter",
        "JIRA_PROJECTS_FILTER": "jira_projects_filter",
        "READ_ONLY_MODE": "read_only_mode", 
        "ENABLED_TOOLS": "enabled_tools",
        "MCP_VERBOSE": "mcp_verbose"
    }
    
    for env_var, config_key in optional_vars.items():
        value = os.getenv(env_var)
        if value:
            if config_key in ["confluence_ssl_verify", "jira_ssl_verify", "read_only_mode", "mcp_verbose"]:
                config_dict[config_key] = value.lower() not in ("false", "0", "no")
            else:
                config_dict[config_key] = value
    
    return AtlassianServerConfig(**config_dict)


def create_oauth_config_from_env() -> AtlassianOAuthConfig:
    """Create OAuth configuration from environment variables"""
    
    required_vars = {
        "CONFLUENCE_URL": "confluence_url",
        "JIRA_URL": "jira_url",
        "ATLASSIAN_OAUTH_CLOUD_ID": "oauth_cloud_id",
        "ATLASSIAN_OAUTH_CLIENT_ID": "oauth_client_id",
        "ATLASSIAN_OAUTH_CLIENT_SECRET": "oauth_client_secret", 
        "ATLASSIAN_OAUTH_REDIRECT_URI": "oauth_redirect_uri",
        "ATLASSIAN_OAUTH_SCOPE": "oauth_scope"
    }
    
    config_dict = {}
    for env_var, config_key in required_vars.items():
        value = os.getenv(env_var)
        if not value:
            raise ValueError(f"Required environment variable {env_var} is not set")
        config_dict[config_key] = value
    
    # Optional variables
    optional_vars = {
        "ATLASSIAN_OAUTH_ACCESS_TOKEN": "oauth_access_token",
        "READ_ONLY_MODE": "read_only_mode",
        "ENABLED_TOOLS": "enabled_tools", 
        "MCP_VERBOSE": "mcp_verbose"
    }
    
    for env_var, config_key in optional_vars.items():
        value = os.getenv(env_var)
        if value:
            if config_key in ["read_only_mode", "mcp_verbose"]:
                config_dict[config_key] = value.lower() in ("true", "1", "yes")
            else:
                config_dict[config_key] = value
    
    return AtlassianOAuthConfig(**config_dict)


def get_recommended_tools() -> Dict[str, List[str]]:
    """Get recommended tool sets for different use cases"""
    
    return {
        "read_only": [
            "confluence_search",
            "confluence_get_page", 
            "confluence_get_page_children",
            "jira_search",
            "jira_get_issue",
            "jira_get_all_projects",
            "jira_get_project_issues"
        ],
        
        "content_management": [
            "confluence_search",
            "confluence_get_page",
            "confluence_create_page",
            "confluence_update_page",
            "confluence_add_comment",
            "jira_search", 
            "jira_get_issue"
        ],
        
        "issue_tracking": [
            "jira_search",
            "jira_get_issue",
            "jira_create_issue",
            "jira_update_issue",
            "jira_add_comment",
            "jira_transition_issue",
            "jira_get_all_projects",
            "confluence_search",
            "confluence_get_page"
        ],
        
        "full_access": None  # All tools enabled
    }


def print_setup_instructions():
    """Print setup instructions for different deployment types"""
    
    print("Atlassian MCP Integration Setup")
    print("=" * 50)
    print()
    
    print("1. Cloud Deployment with API Tokens:")
    print("   export CONFLUENCE_URL='https://your-company.atlassian.net/wiki'")
    print("   export CONFLUENCE_USERNAME='your.email@company.com'")
    print("   export CONFLUENCE_API_TOKEN='your_confluence_api_token'")
    print("   export JIRA_URL='https://your-company.atlassian.net'") 
    print("   export JIRA_USERNAME='your.email@company.com'")
    print("   export JIRA_API_TOKEN='your_jira_api_token'")
    print()
    
    print("2. Server/Data Center with Personal Access Tokens:")
    print("   export CONFLUENCE_URL='https://confluence.your-company.com'")
    print("   export CONFLUENCE_PERSONAL_TOKEN='your_confluence_pat'")
    print("   export JIRA_URL='https://jira.your-company.com'")
    print("   export JIRA_PERSONAL_TOKEN='your_jira_pat'")
    print("   # For self-signed certificates:")
    print("   export CONFLUENCE_SSL_VERIFY='false'")
    print("   export JIRA_SSL_VERIFY='false'")
    print()
    
    print("3. OAuth 2.0 (Cloud only):")
    print("   export CONFLUENCE_URL='https://your-company.atlassian.net/wiki'")
    print("   export JIRA_URL='https://your-company.atlassian.net'")
    print("   export ATLASSIAN_OAUTH_CLOUD_ID='your_cloud_id'")
    print("   export ATLASSIAN_OAUTH_CLIENT_ID='your_oauth_client_id'") 
    print("   export ATLASSIAN_OAUTH_CLIENT_SECRET='your_oauth_client_secret'")
    print("   export ATLASSIAN_OAUTH_REDIRECT_URI='http://localhost:8080/callback'")
    print("   export ATLASSIAN_OAUTH_SCOPE='read:jira-work write:jira-work read:confluence-content.all write:confluence-content offline_access'")
    print()
    
    print("Optional Configuration:")
    print("   export CONFLUENCE_SPACES_FILTER='DEV,TEAM,DOC'")
    print("   export JIRA_PROJECTS_FILTER='PROJ,DEV,SUPPORT'")
    print("   export READ_ONLY_MODE='false'")
    print("   export MCP_VERBOSE='true'")
    print("   export ENABLED_TOOLS='confluence_search,jira_get_issue,jira_search'")
    print()
    
    print("Make sure Docker is installed and the mcp-atlassian image is available:")
    print("   docker pull ghcr.io/sooperset/mcp-atlassian:latest")


if __name__ == "__main__":
    print_setup_instructions()