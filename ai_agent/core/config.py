import os
from typing import Optional, List
from pydantic import BaseSettings, Field, validator


class Config(BaseSettings):
    """Configuration management for the AI agent"""
    
    # API Configuration
    custom_ai_api_url: str = Field(..., env="CUSTOM_AI_API_URL")
    custom_ai_api_key: str = Field(..., env="CUSTOM_AI_API_KEY")
    custom_ai_model: str = Field(default="gpt-4", env="CUSTOM_AI_MODEL")
    custom_ai_max_tokens: int = Field(default=2000, env="CUSTOM_AI_MAX_TOKENS")
    custom_ai_temperature: float = Field(default=0.7, env="CUSTOM_AI_TEMPERATURE")
    
    # Confluence Configuration
    confluence_access_token: str = Field(..., env="CONFLUENCE_ACCESS_TOKEN")
    confluence_base_url: str = Field(..., env="CONFLUENCE_BASE_URL")
    confluence_spaces: Optional[List[str]] = Field(default=None, env="CONFLUENCE_SPACES")
    confluence_timeout: float = Field(default=30.0, env="CONFLUENCE_TIMEOUT")
    confluence_max_retries: int = Field(default=3, env="CONFLUENCE_MAX_RETRIES")
    confluence_content_types: List[str] = Field(default=["page", "blogpost"], env="CONFLUENCE_CONTENT_TYPES")
    
    # JIRA Configuration
    jira_access_token: str = Field(..., env="JIRA_ACCESS_TOKEN")
    jira_base_url: str = Field(..., env="JIRA_BASE_URL")
    jira_projects: Optional[List[str]] = Field(default=None, env="JIRA_PROJECTS")
    jira_issue_key_prefixes: Optional[List[str]] = Field(default=None, env="JIRA_ISSUE_KEY_PREFIXES")
    jira_timeout: float = Field(default=30.0, env="JIRA_TIMEOUT")
    jira_max_retries: int = Field(default=3, env="JIRA_MAX_RETRIES")
    jira_fields: List[str] = Field(default=[
        'summary', 'description', 'status', 'assignee', 'reporter', 
        'priority', 'created', 'updated', 'resolutiondate', 'project',
        'issuetype', 'labels', 'components', 'fixVersions'
    ], env="JIRA_FIELDS")
    
    # Code Repository Configuration
    code_repo_path: str = Field(default="./", env="CODE_REPO_PATH")
    code_supported_extensions: List[str] = Field(default=[
        ".java", ".py", ".js", ".ts", ".json", ".yaml", ".yml", ".xml", 
        ".sh", ".bash", ".sql", ".md", ".txt", ".properties", ".conf"
    ], env="CODE_SUPPORTED_EXTENSIONS")
    code_exclude_patterns: List[str] = Field(default=[
        "node_modules/*", "target/*", "build/*", "dist/*", ".git/*",
        "*.log", "*.tmp", "*.cache", ".env", ".env.*"
    ], env="CODE_EXCLUDE_PATTERNS")
    code_exclude_paths: List[str] = Field(default=[], env="CODE_EXCLUDE_PATHS")
    code_max_file_size: int = Field(default=1048576, env="CODE_MAX_FILE_SIZE")  # 1MB default
    
    # MCP Server Configuration
    confluence_mcp_server_url: str = Field(..., env="CONFLUENCE_MCP_SERVER_URL")
    jira_mcp_server_url: str = Field(..., env="JIRA_MCP_SERVER_URL")
    
    # Cache Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    cache_ttl_short: int = Field(default=300, env="CACHE_TTL_SHORT")  # 5 minutes
    cache_ttl_medium: int = Field(default=1800, env="CACHE_TTL_MEDIUM")  # 30 minutes
    cache_ttl_long: int = Field(default=3600, env="CACHE_TTL_LONG")  # 1 hour
    enable_file_cache: bool = Field(default=True, env="ENABLE_FILE_CACHE")
    file_cache_dir: str = Field(default="./cache", env="FILE_CACHE_DIR")
    
    # Monitoring Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_workers: int = Field(default=4, env="API_WORKERS")
    enable_cors: bool = Field(default=True, env="ENABLE_CORS")
    
    @validator('confluence_spaces', pre=True)
    def parse_confluence_spaces(cls, v):
        if isinstance(v, str):
            # Parse JSON array or comma-separated string
            if v.strip().startswith('['):
                import json
                return json.loads(v)
            else:
                return [space.strip() for space in v.split(',') if space.strip()]
        return v
    
    @validator('jira_projects', pre=True)
    def parse_jira_projects(cls, v):
        if isinstance(v, str):
            # Parse JSON array or comma-separated string
            if v.strip().startswith('['):
                import json
                return json.loads(v)
            else:
                return [project.strip() for project in v.split(',') if project.strip()]
        return v
    
    @validator('jira_issue_key_prefixes', pre=True)
    def parse_jira_issue_key_prefixes(cls, v):
        if isinstance(v, str):
            # Parse JSON array or comma-separated string
            if v.strip().startswith('['):
                import json
                return json.loads(v)
            else:
                return [prefix.strip().upper() for prefix in v.split(',') if prefix.strip()]
        elif isinstance(v, list):
            # Ensure all prefixes are uppercase for consistency
            return [prefix.strip().upper() for prefix in v if prefix.strip()]
        return v
    
    @validator('code_supported_extensions', pre=True)
    def parse_code_extensions(cls, v):
        if isinstance(v, str):
            if v.strip().startswith('['):
                import json
                return json.loads(v)
            else:
                return [ext.strip() for ext in v.split(',') if ext.strip()]
        return v
    
    @validator('code_exclude_patterns', pre=True)
    def parse_exclude_patterns(cls, v):
        if isinstance(v, str):
            if v.strip().startswith('['):
                import json
                return json.loads(v)
            else:
                return [pattern.strip() for pattern in v.split(',') if pattern.strip()]
        return v
    
    @validator('code_exclude_paths', pre=True)
    def parse_exclude_paths(cls, v):
        if isinstance(v, str):
            if v.strip().startswith('['):
                import json
                return json.loads(v)
            else:
                return [path.strip() for path in v.split(',') if path.strip()]
        return v
    
    @validator('confluence_content_types', pre=True)
    def parse_content_types(cls, v):
        if isinstance(v, str):
            if v.strip().startswith('['):
                import json
                return json.loads(v)
            else:
                return [ctype.strip() for ctype in v.split(',') if ctype.strip()]
        return v
    
    @validator('jira_fields', pre=True)
    def parse_jira_fields(cls, v):
        if isinstance(v, str):
            if v.strip().startswith('['):
                import json
                return json.loads(v)
            else:
                return [field.strip() for field in v.split(',') if field.strip()]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


def load_config() -> Config:
    """Load configuration from environment variables"""
    return Config()