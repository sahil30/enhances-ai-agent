"""
Type definitions and structured data models for the AI Agent

This module provides comprehensive type definitions using modern Python typing patterns,
including TypedDict for structured data and proper generic types.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import (
    TypedDict, 
    Optional, 
    List, 
    Dict, 
    Any, 
    Union, 
    Literal,
    Protocol,
    TypeVar,
    Generic,
    NewType
)
from dataclasses import dataclass
from pathlib import Path

# Custom type aliases
UserId = NewType('UserId', str)
IssueKey = NewType('IssueKey', str)  # e.g., "PROJ-123"
PageId = NewType('PageId', str)     # Confluence page ID
FilePath = NewType('FilePath', str)
QueryString = NewType('QueryString', str)
RelevanceScore = NewType('RelevanceScore', float)  # 0.0 to 1.0
ConfidenceScore = NewType('ConfidenceScore', float)  # 0.0 to 1.0

# Generic type variables
T = TypeVar('T')
SearchResultT = TypeVar('SearchResultT', bound='BaseSearchResult')


class SourceType(str, Enum):
    """Enumeration of data source types"""
    CONFLUENCE = "confluence"
    JIRA = "jira"
    CODE = "code"


# QueryType and QueryIntent are defined in query_processor.py to avoid circular imports
# Import them from there when needed


class ProblemCategory(str, Enum):
    """Categories of problems the agent can help with"""
    AUTHENTICATION = "authentication"
    PERFORMANCE = "performance"
    ERROR_DEBUGGING = "error_debugging"
    DEPLOYMENT = "deployment"
    DATABASE = "database"
    API_INTEGRATION = "api_integration"
    CONFIGURATION = "configuration"
    SECURITY = "security"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    GENERAL = "general"


class Urgency(str, Enum):
    """Urgency levels for problems"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Complexity(str, Enum):
    """Complexity levels for problems"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class LogLevel(str, Enum):
    """Logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# TypedDict definitions for structured data
class BaseSearchResult(TypedDict):
    """Base structure for all search results"""
    id: str
    title: str
    url: Optional[str]
    source: SourceType
    relevance_score: RelevanceScore
    created: Optional[datetime]
    updated: Optional[datetime]
    author: Optional[str]
    content_preview: str


class ConfluenceSearchResult(BaseSearchResult):
    """Confluence-specific search result"""
    source: Literal[SourceType.CONFLUENCE]
    space_key: Optional[str]
    space_name: Optional[str]
    page_id: PageId
    content_type: str  # "page", "blogpost", etc.
    excerpt: str
    labels: List[str]
    restrictions: Dict[str, Any]


class JiraSearchResult(BaseSearchResult):
    """JIRA-specific search result"""
    source: Literal[SourceType.JIRA]
    issue_key: IssueKey
    project_key: str
    project_name: str
    issue_type: str
    status: str
    priority: str
    assignee: Optional[str]
    reporter: Optional[str]
    resolution: Optional[str]
    components: List[str]
    labels: List[str]
    fix_versions: List[str]
    description: Optional[str]


class CodeSearchResult(BaseSearchResult):
    """Code repository search result"""
    source: Literal[SourceType.CODE]
    file_path: FilePath
    relative_path: str
    file_type: str  # File extension
    file_size: int
    line_number: Optional[int]
    match_context: str  # Surrounding code context
    programming_language: Optional[str]
    git_info: Optional[Dict[str, Any]]


class ProblemAnalysis(TypedDict):
    """Analysis of user problem/query"""
    query_type: QueryType
    intent: QueryIntent
    problem_category: ProblemCategory
    technical_terms: List[str]
    urgency: Urgency
    complexity: Complexity
    keywords: List[str]
    entities: List[str]
    confidence: ConfidenceScore


class SearchStrategy(TypedDict):
    """Search strategy configuration"""
    search_confluence: bool
    search_jira: bool
    search_code: bool
    max_results: int
    file_types: Optional[List[str]]
    confluence_spaces: Optional[List[str]]
    jira_projects: Optional[List[str]]
    jira_key_prefixes: Optional[List[str]]
    priority_boost: Dict[SourceType, float]


class UserContext(TypedDict):
    """User/team context for personalization"""
    user_id: Optional[UserId]
    team_keywords: Optional[List[str]]
    projects: Optional[List[str]]
    spaces: Optional[List[str]]
    problem_category: ProblemCategory
    technical_terms: List[str]
    urgency: Urgency
    complexity: Complexity
    search_preferences: SearchStrategy
    context_timestamp: str


class RankingFactors(TypedDict):
    """Factors used in result ranking"""
    content_relevance: float
    recency_score: float
    team_relevance: float
    quality_score: float
    cross_correlation_boost: float
    final_score: float


class CrossCorrelation(TypedDict):
    """Cross-source correlation information"""
    source_1: SourceType
    result_1_id: str
    source_2: SourceType
    result_2_id: str
    correlation_type: str
    strength: float
    description: str


class RankingInsights(TypedDict):
    """Insights about ranking quality"""
    total_results: int
    avg_relevance: float
    avg_recency: float
    avg_quality: float
    cross_correlations: int
    strong_correlations: int
    recommendations: List[str]


class SolutionComponent(TypedDict):
    """Component of a solution"""
    title: str
    description: str
    implementation_steps: List[str]
    code_examples: Optional[List[str]]
    risks: List[str]
    related_resources: List[str]


class ComprehensiveSolution(TypedDict):
    """Complete solution structure"""
    summary: str
    components: List[SolutionComponent]
    implementation_steps: List[str]
    risks: List[str]
    related_issues: List[str]
    confidence: ConfidenceScore
    estimated_effort: str
    prerequisites: List[str]


class SearchResponse(TypedDict):
    """Complete search response structure"""
    query: QueryString
    problem_analysis: ProblemAnalysis
    solution: ComprehensiveSolution
    sources: Dict[SourceType, Dict[str, Any]]
    search_strategy: SearchStrategy
    ranking_insights: RankingInsights
    cross_correlations: List[CrossCorrelation]
    metadata: Dict[str, Any]


class HealthCheckStatus(TypedDict):
    """Health check status"""
    service: str
    status: Literal["healthy", "unhealthy", "degraded"]
    response_time: Optional[float]
    error: Optional[str]
    last_check: datetime


class SystemHealth(TypedDict):
    """Overall system health"""
    status: Literal["healthy", "unhealthy", "degraded"]
    timestamp: datetime
    version: str
    checks: Dict[str, HealthCheckStatus]
    warnings: List[str]


# Protocol definitions for dependency injection
class ConfigProtocol(Protocol):
    """Protocol for configuration objects"""
    custom_ai_api_url: str
    custom_ai_api_key: str
    confluence_access_token: str
    jira_access_token: str


class AIClientProtocol(Protocol):
    """Protocol for AI client implementations"""
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: Optional[int] = None
    ) -> str: ...
    
    async def close(self) -> None: ...


class MCPClientProtocol(Protocol):
    """Protocol for MCP client implementations"""
    async def connect(self) -> None: ...
    async def disconnect(self) -> None: ...
    async def send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]: ...


class CacheProtocol(Protocol):
    """Protocol for cache implementations"""
    async def get(self, key: str) -> Optional[Any]: ...
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None: ...
    async def delete(self, key: str) -> None: ...
    async def clear(self) -> None: ...


# Generic result container
@dataclass
class SearchResultContainer(Generic[T]):
    """Generic container for search results with metadata"""
    results: List[T]
    total_count: int
    query_time_ms: float
    source: SourceType
    has_more: bool = False
    next_page_token: Optional[str] = None


# Exception types
class AIAgentError(Exception):
    """Base exception for AI Agent errors"""
    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.error_code = error_code


class ConfigurationError(AIAgentError):
    """Configuration-related errors"""
    pass


class MCPConnectionError(AIAgentError):
    """MCP connection errors"""
    pass


class SearchError(AIAgentError):
    """Search operation errors"""
    pass


class ValidationError(AIAgentError):
    """Input validation errors"""
    pass


# Utility type guards
def is_confluence_result(result: BaseSearchResult) -> bool:
    """Type guard for Confluence results"""
    return result['source'] == SourceType.CONFLUENCE


def is_jira_result(result: BaseSearchResult) -> bool:
    """Type guard for JIRA results"""
    return result['source'] == SourceType.JIRA


def is_code_result(result: BaseSearchResult) -> bool:
    """Type guard for code results"""
    return result['source'] == SourceType.CODE


# Type narrowing functions
def as_confluence_result(result: BaseSearchResult) -> ConfluenceSearchResult:
    """Narrow type to ConfluenceSearchResult"""
    if not is_confluence_result(result):
        raise TypeError(f"Expected Confluence result, got {result['source']}")
    return result  # type: ignore


def as_jira_result(result: BaseSearchResult) -> JiraSearchResult:
    """Narrow type to JiraSearchResult"""
    if not is_jira_result(result):
        raise TypeError(f"Expected JIRA result, got {result['source']}")
    return result  # type: ignore


def as_code_result(result: BaseSearchResult) -> CodeSearchResult:
    """Narrow type to CodeSearchResult"""
    if not is_code_result(result):
        raise TypeError(f"Expected code result, got {result['source']}")
    return result  # type: ignore