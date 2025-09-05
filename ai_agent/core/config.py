import os
from typing import Optional
from pydantic import BaseSettings, Field


class Config(BaseSettings):
    """Configuration management for the AI agent"""
    
    # API Configuration
    custom_ai_api_url: str = Field(..., env="CUSTOM_AI_API_URL")
    custom_ai_api_key: str = Field(..., env="CUSTOM_AI_API_KEY")
    
    # Confluence Configuration
    confluence_access_token: str = Field(..., env="CONFLUENCE_ACCESS_TOKEN")
    confluence_base_url: str = Field(..., env="CONFLUENCE_BASE_URL")
    
    # JIRA Configuration
    jira_access_token: str = Field(..., env="JIRA_ACCESS_TOKEN")
    jira_base_url: str = Field(..., env="JIRA_BASE_URL")
    
    # Code Repository Configuration
    code_repo_path: str = Field(default="./", env="CODE_REPO_PATH")
    
    # MCP Server Configuration
    confluence_mcp_server_url: str = Field(..., env="CONFLUENCE_MCP_SERVER_URL")
    jira_mcp_server_url: str = Field(..., env="JIRA_MCP_SERVER_URL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


def load_config() -> Config:
    """Load configuration from environment variables"""
    return Config()