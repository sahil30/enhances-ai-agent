"""
Configuration management for the AI agent using Pydantic v2 patterns
"""
from __future__ import annotations

import json
import os
from typing import Optional, List, Union, Any
from pathlib import Path

from pydantic import BaseModel, Field, field_validator, ConfigDict, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_list_from_string_or_json(value: Union[str, List[str], None]) -> Optional[List[str]]:
    """
    Generic parser for list values that can come as JSON arrays or comma-separated strings
    
    Args:
        value: String (JSON or comma-separated), list, or None
    
    Returns:
        Parsed list or None
    
    Raises:
        ValueError: If JSON parsing fails
    """
    if value is None:
        return None
    
    if isinstance(value, list):
        return [item.strip() for item in value if item.strip()]
    
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
            
        # Parse JSON array
        if value.startswith('[') and value.endswith(']'):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
                else:
                    raise ValueError(f"Expected list, got {type(parsed)}")
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON array: {e}")
        
        # Parse comma-separated string
        return [item.strip() for item in value.split(',') if item.strip()]
    
    raise ValueError(f"Expected string or list, got {type(value)}")


class CacheConfig(BaseModel):
    """Cache configuration settings"""
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    ttl_short: int = Field(default=300, ge=60, description="Short-term cache TTL in seconds (min 60s)")
    ttl_medium: int = Field(default=1800, ge=300, description="Medium-term cache TTL in seconds (min 5m)")
    ttl_long: int = Field(default=3600, ge=900, description="Long-term cache TTL in seconds (min 15m)")
    enable_file_cache: bool = Field(default=True, description="Enable file-based caching")
    file_cache_dir: Path = Field(default=Path("./cache"), description="File cache directory")


class MonitoringConfig(BaseModel):
    """Monitoring and observability configuration"""
    log_level: str = Field(default="INFO", description="Logging level")
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    metrics_port: int = Field(default=9090, ge=1024, le=65535, description="Metrics server port")
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()


class APIConfig(BaseModel):
    """API server configuration"""
    host: str = Field(default="0.0.0.0", description="API server host")
    port: int = Field(default=8000, ge=1024, le=65535, description="API server port")
    workers: int = Field(default=4, ge=1, le=32, description="Number of worker processes")
    enable_cors: bool = Field(default=True, description="Enable CORS support")


class Config(BaseSettings):
    """
    Main configuration class for the AI agent using Pydantic v2 patterns
    
    All configuration can be provided via environment variables or .env file
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',  # Allow unknown fields (for backward compatibility)
        validate_assignment=True  # Validate on assignment
    )
    
    # AI API Configuration
    custom_ai_api_url: str = Field(..., description="Custom AI API endpoint URL")
    custom_ai_api_key: str = Field(..., description="API key for custom AI service")
    custom_ai_model: str = Field(default="gpt-4", description="AI model to use")
    custom_ai_max_tokens: int = Field(default=2000, ge=100, le=8000, description="Maximum tokens per request")
    custom_ai_temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="AI response temperature")
    
    # Confluence Configuration
    confluence_access_token: str = Field(..., description="Confluence API access token")
    confluence_base_url: str = Field(..., description="Confluence base URL")
    confluence_spaces: Optional[List[str]] = Field(default=None, description="Confluence spaces to search")
    confluence_timeout: float = Field(default=30.0, ge=5.0, le=300.0, description="Request timeout in seconds")
    confluence_max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")
    confluence_content_types: List[str] = Field(
        default=["page", "blogpost"], 
        description="Content types to search"
    )
    
    # JIRA Configuration  
    jira_access_token: str = Field(..., description="JIRA API access token")
    jira_base_url: str = Field(..., description="JIRA base URL")
    jira_projects: Optional[List[str]] = Field(default=None, description="JIRA projects to search")
    jira_issue_key_prefixes: Optional[List[str]] = Field(
        default=None, 
        description="JIRA issue key prefixes for team-specific filtering"
    )
    jira_timeout: float = Field(default=30.0, ge=5.0, le=300.0, description="Request timeout in seconds")
    jira_max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")
    jira_fields: List[str] = Field(
        default=[
            'summary', 'description', 'status', 'assignee', 'reporter', 
            'priority', 'created', 'updated', 'resolutiondate', 'project',
            'issuetype', 'labels', 'components', 'fixVersions'
        ],
        description="JIRA fields to retrieve"
    )
    
    # Code Repository Configuration
    code_repo_path: Path = Field(default=Path("./"), description="Path to code repository")
    code_supported_extensions: List[str] = Field(
        default=[
            ".java", ".py", ".js", ".ts", ".json", ".yaml", ".yml", ".xml", 
            ".sh", ".bash", ".sql", ".md", ".txt", ".properties", ".conf"
        ],
        description="Supported file extensions for code search"
    )
    code_exclude_patterns: List[str] = Field(
        default=[
            "node_modules/*", "target/*", "build/*", "dist/*", ".git/*",
            "*.log", "*.tmp", "*.cache", ".env", ".env.*"
        ],
        description="File patterns to exclude from code search"
    )
    code_exclude_paths: List[str] = Field(default=[], description="Specific paths to exclude")
    code_max_file_size: int = Field(
        default=1048576, 
        ge=1024, 
        le=10485760,  # 10MB max
        description="Maximum file size to process (bytes)"
    )
    
    # MCP Server Configuration
    confluence_mcp_server_url: str = Field(..., description="Confluence MCP server WebSocket URL")
    jira_mcp_server_url: str = Field(..., description="JIRA MCP server WebSocket URL")
    
    # Direct cache configuration fields (for backward compatibility)
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    enable_file_cache: bool = Field(default=True, description="Enable file-based caching")
    file_cache_dir: Path = Field(default=Path("./cache"), description="File cache directory")
    cache_ttl_short: int = Field(default=300, ge=60, description="Short-term cache TTL in seconds")
    cache_ttl_medium: int = Field(default=1800, ge=300, description="Medium-term cache TTL in seconds")
    cache_ttl_long: int = Field(default=3600, ge=900, description="Long-term cache TTL in seconds")
    
    # Direct monitoring fields (for backward compatibility)
    log_level: str = Field(default="INFO", description="Logging level")
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    metrics_port: int = Field(default=9090, ge=1024, le=65535, description="Metrics server port")
    
    # Direct API configuration fields (for backward compatibility)
    enable_cors: bool = Field(default=True, description="Enable CORS support")
    api_host: str = Field(default="0.0.0.0", description="API server host")
    api_port: int = Field(default=8000, ge=1024, le=65535, description="API server port")
    api_workers: int = Field(default=4, ge=1, le=32, description="Number of worker processes")
    
    # Nested configuration objects (computed properties)
    @property
    def cache(self) -> CacheConfig:
        """Get cache configuration from direct fields"""
        return CacheConfig(
            redis_url=self.redis_url,
            ttl_short=self.cache_ttl_short,
            ttl_medium=self.cache_ttl_medium,
            ttl_long=self.cache_ttl_long,
            enable_file_cache=self.enable_file_cache,
            file_cache_dir=self.file_cache_dir
        )
    
    @property
    def monitoring(self) -> MonitoringConfig:
        """Get monitoring configuration from direct fields"""
        return MonitoringConfig(
            log_level=self.log_level,
            enable_metrics=self.enable_metrics,
            metrics_port=self.metrics_port
        )
    
    @property
    def api(self) -> APIConfig:
        """Get API configuration from direct fields"""
        return APIConfig(
            host=self.api_host,
            port=self.api_port,
            workers=self.api_workers,
            enable_cors=self.enable_cors
        )
    
    # Validation and parsing
    @field_validator('custom_ai_api_url', 'confluence_base_url', 'jira_base_url', 'confluence_mcp_server_url', 'jira_mcp_server_url')
    @classmethod
    def validate_urls(cls, v: str) -> str:
        """Validate URL format"""
        if not v or not isinstance(v, str):
            raise ValueError("URL cannot be empty")
        
        v = v.strip()
        if not (v.startswith('http://') or v.startswith('https://') or v.startswith('ws://') or v.startswith('wss://')):
            raise ValueError("URL must start with http://, https://, ws://, or wss://")
        
        return v
    
    @field_validator('confluence_spaces', 'jira_projects', 'confluence_content_types', 'jira_fields', 
                     'code_supported_extensions', 'code_exclude_patterns', 'code_exclude_paths', mode='before')
    @classmethod
    def parse_list_fields(cls, v: Any) -> Optional[List[str]]:
        """Parse list fields from various input formats"""
        try:
            return parse_list_from_string_or_json(v)
        except ValueError as e:
            raise ValueError(f"Invalid list format: {e}")
    
    @field_validator('jira_issue_key_prefixes', mode='before')
    @classmethod
    def parse_and_uppercase_prefixes(cls, v: Any) -> Optional[List[str]]:
        """Parse and uppercase JIRA issue key prefixes"""
        try:
            parsed = parse_list_from_string_or_json(v)
            if parsed is not None:
                return [prefix.strip().upper() for prefix in parsed if prefix.strip()]
            return None
        except ValueError as e:
            raise ValueError(f"Invalid JIRA issue key prefixes format: {e}")
    
    @field_validator('code_repo_path')
    @classmethod
    def validate_code_repo_path(cls, v: Path) -> Path:
        """Validate code repository path exists"""
        if not v.exists():
            raise ValueError(f"Code repository path does not exist: {v}")
        if not v.is_dir():
            raise ValueError(f"Code repository path is not a directory: {v}")
        return v.resolve()  # Return absolute path
    
    @field_validator('code_supported_extensions', mode='after')
    @classmethod
    def validate_extensions(cls, v: List[str]) -> List[str]:
        """Validate file extensions format"""
        validated = []
        for ext in v:
            ext = ext.strip()
            if not ext.startswith('.'):
                ext = '.' + ext
            if len(ext) < 2:
                raise ValueError(f"Invalid file extension: {ext}")
            validated.append(ext.lower())
        return validated
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    @field_validator('custom_ai_api_key', 'confluence_access_token', 'jira_access_token')
    @classmethod
    def validate_secrets(cls, v: str) -> str:
        """Validate secret fields are not empty"""
        if not v or not v.strip():
            raise ValueError("Secret field cannot be empty")
        return v.strip()


def load_config() -> Config:
    """
    Load configuration from environment variables and .env file
    
    Returns:
        Validated Config instance
        
    Raises:
        ValidationError: If configuration validation fails
    """
    try:
        return Config()
    except ValidationError as e:
        # Format validation errors nicely
        error_details = []
        for error in e.errors():
            field = " -> ".join(str(x) for x in error['loc'])
            error_details.append(f"{field}: {error['msg']}")
        
        raise ValueError(f"Configuration validation failed:\n" + "\n".join(error_details)) from e


def validate_config(config: Config) -> List[str]:
    """
    Additional runtime validation and warnings
    
    Args:
        config: Config instance to validate
        
    Returns:
        List of warning messages
    """
    warnings = []
    
    # Check cache directory permissions
    if config.cache.enable_file_cache:
        try:
            config.cache.file_cache_dir.mkdir(parents=True, exist_ok=True)
            test_file = config.cache.file_cache_dir / ".write_test"
            test_file.touch()
            test_file.unlink()
        except Exception:
            warnings.append(f"File cache directory is not writable: {config.cache.file_cache_dir}")
    
    # Validate timeout relationships
    if config.confluence_timeout > 120:
        warnings.append("Confluence timeout > 2 minutes may cause performance issues")
    
    if config.jira_timeout > 120:
        warnings.append("JIRA timeout > 2 minutes may cause performance issues")
    
    # Check reasonable limits
    if config.custom_ai_max_tokens > 4000:
        warnings.append("Very high max_tokens may result in expensive API calls")
    
    if config.code_max_file_size > 5242880:  # 5MB
        warnings.append("Large max_file_size may cause memory issues with big files")
    
    return warnings