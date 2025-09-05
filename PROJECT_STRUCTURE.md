# AI Agent Project Structure

This document describes the organized file structure and functionality groupings of the AI Agent project.

## Directory Organization

```
ai_agent/
├── __init__.py                 # Main package exports
├── core/                       # Core business logic
│   ├── __init__.py
│   ├── agent.py               # Main AIAgent orchestrator
│   ├── config.py              # Configuration management
│   ├── ai_client.py           # Custom AI API client
│   ├── code_reader.py         # Code repository analysis
│   └── query_processor.py     # NLP query processing
├── mcp/                       # MCP (Model Context Protocol) integration
│   ├── __init__.py
│   ├── base/                  # Base MCP functionality
│   │   ├── __init__.py
│   │   ├── mcp_base.py        # Base MCP client & connection handling
│   │   └── utils.py           # MCP utility functions & formatters
│   └── clients/               # Specialized MCP client implementations
│       ├── __init__.py
│       ├── confluence_client.py # Confluence-specific MCP client
│       └── jira_client.py     # JIRA-specific MCP client
├── infrastructure/            # System services & utilities
│   ├── __init__.py
│   ├── cache_manager.py       # Multi-tier caching system
│   ├── reliability.py         # Circuit breakers & retry logic
│   ├── monitoring.py          # Logging, metrics, monitoring
│   ├── batch_processor.py     # Concurrent batch processing
│   ├── semantic_search.py     # Advanced search & ranking
│   └── health_checks.py       # Health monitoring & validation
├── api/                       # User interfaces
│   ├── __init__.py
│   ├── web_api.py             # FastAPI REST endpoints
│   └── cli.py                 # Command-line interface
├── plugins/                   # Extensible plugin system
│   ├── __init__.py
│   └── plugin_system.py       # Plugin architecture
└── tests/                     # Comprehensive test suite
    ├── __init__.py
    ├── test_agent.py          # Core agent tests
    ├── test_cache.py          # Caching system tests
    ├── test_query_processor.py # NLP processing tests
    └── test_web_api.py        # API endpoint tests

# Root level files
├── main.py                    # CLI entry point
├── start_api.py              # Web API server entry point
├── requirements.txt          # Python dependencies
├── pytest.ini              # Test configuration
├── .env.example            # Environment variables template
├── README.md               # Comprehensive documentation
└── PROJECT_STRUCTURE.md   # This file
```

## Functional Groups

### 1. **Core Module** (`ai_agent/core/`)
**Purpose**: Contains the primary business logic and core AI agent functionality.

- **`agent.py`**: Main orchestrator that coordinates searches across Confluence, JIRA, and code repositories
- **`config.py`**: Configuration management with Pydantic validation and environment variable handling
- **`ai_client.py`**: Integration with custom AI APIs for context analysis and solution generation
- **MCP Integration**: Dedicated MCP module with specialized client implementations (see MCP Module section)
- **`code_reader.py`**: Multi-language code analysis (Java, Python, JSON, Shell scripts)
- **`query_processor.py`**: NLP-powered query analysis with intent recognition and semantic understanding

### 2. **MCP Module** (`ai_agent/mcp/`)
**Purpose**: Model Context Protocol (MCP) server integration and communication.

#### Base Components (`ai_agent/mcp/base/`)
- **`mcp_base.py`**: Foundation MCP client with WebSocket communication, connection management, retry logic, and health monitoring
- **`utils.py`**: MCP utility functions including response formatting, parameter validation, HTML cleaning, and relevance scoring

#### Client Implementations (`ai_agent/mcp/clients/`)
- **`confluence_client.py`**: Specialized Confluence MCP client with:
  - Page and blog post searching with CQL (Confluence Query Language)
  - Content retrieval with full metadata and formatting
  - Space-based filtering and label-based searching
  - Advanced result formatting and relevance scoring

- **`jira_client.py`**: Specialized JIRA MCP client with:
  - Issue searching using JQL (JIRA Query Language) 
  - Detailed issue retrieval with comments, attachments, and changelog
  - Project-based filtering and component-based searching
  - User-centric issue queries (assigned/reported)

### 3. **Infrastructure Module** (`ai_agent/infrastructure/`)
**Purpose**: System-level services, reliability patterns, and supporting infrastructure.

- **`cache_manager.py`**: Multi-tier caching (memory, Redis, file) with intelligent TTL management
- **`reliability.py`**: Circuit breaker patterns, retry logic, and fault tolerance mechanisms
- **`monitoring.py`**: Structured logging, Prometheus metrics collection, and performance monitoring
- **`batch_processor.py`**: Concurrent query processing with priority queues and worker pools
- **`semantic_search.py`**: TF-IDF vectorization, SVD dimensionality reduction, and similarity ranking
- **`health_checks.py`**: Configuration validation, system health monitoring, and diagnostics

### 4. **API Module** (`ai_agent/api/`)
**Purpose**: User-facing interfaces and API endpoints.

- **`web_api.py`**: FastAPI-based REST API with async support, OpenAPI docs, and comprehensive endpoints
- **`cli.py`**: Command-line interface with Click framework for interactive usage

### 5. **Plugins Module** (`ai_agent/plugins/`)
**Purpose**: Extensible plugin architecture for custom integrations.

- **`plugin_system.py`**: Plugin base classes, lifecycle management, and dynamic loading system

### 6. **Tests Module** (`ai_agent/tests/`)
**Purpose**: Comprehensive test coverage for all components.

- **`test_agent.py`**: Tests for core agent functionality and orchestration
- **`test_cache.py`**: Caching system behavior and performance tests
- **`test_query_processor.py`**: NLP processing and query optimization tests
- **`test_web_api.py`**: API endpoint validation and integration tests

## Entry Points

### CLI Usage
```bash
# Use main.py for command-line operations
python main.py search "authentication issues"
python main.py config-check
python main.py analyze-repo --repo-path ./code
```

### Web API Usage
```bash
# Use start_api.py for web server
python start_api.py --host 0.0.0.0 --port 8000
```

### Programmatic Usage
```python
# Import from organized modules
from ai_agent import AIAgent, load_config
from ai_agent.infrastructure import CacheManager, semantic_search
from ai_agent.plugins import plugin_manager

# Initialize and use
config = load_config()
agent = AIAgent(config)
result = await agent.process_query("How to fix authentication?")
```

## Key Benefits of This Structure

### 1. **Separation of Concerns**
- Core business logic separated from infrastructure concerns
- **MCP integration isolated** into dedicated module with service-specific implementations
- API layers isolated from implementation details
- Plugin system decoupled from core functionality

### 2. **Scalability**
- Infrastructure components can be scaled independently
- **MCP clients can be optimized and scaled per service** (Confluence vs JIRA)
- Plugin system allows extension without core modifications
- Clean interfaces enable horizontal scaling

### 3. **Maintainability**
- Related functionality grouped together
- **Service-specific MCP logic** contained in dedicated client files
- Clear dependency hierarchy
- Easy to locate and modify specific features

### 4. **Testability**
- Each module can be tested in isolation
- Mock dependencies easily injected
- Comprehensive test coverage achievable

### 5. **Extensibility**
- Plugin system supports custom data sources
- **MCP module supports adding new service integrations** (Slack, Teams, etc.)
- Infrastructure components are replaceable
- API can be extended with new endpoints

## Import Patterns

### Internal Imports
```python
# Core to core
from .config import load_config

# API to core
from ..core.agent import AIAgent

# API to MCP
from ..mcp import ConfluenceMCPClient, JiraMCPClient

# API to infrastructure  
from ..infrastructure.cache_manager import CacheManager
```

### External Usage
```python
# Clean public API
from ai_agent import AIAgent, Config
from ai_agent.mcp import ConfluenceMCPClient, JiraMCPClient
from ai_agent.infrastructure import semantic_search
from ai_agent.plugins import plugin_manager
```

This organized structure makes the AI Agent project more maintainable, scalable, and easier to understand while preserving all the advanced functionality that was built.