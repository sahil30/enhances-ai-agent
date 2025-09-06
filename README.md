# AI Agent with Confluence, JIRA, and Code Repository Integration

An enterprise-grade intelligent AI agent that searches across Confluence documentation, JIRA issues, and code repositories to provide comprehensive solution proposals based on user queries.

## Features

### Core Functionality
- **Multi-source Search**: Simultaneously searches Confluence, JIRA, and code repositories
- **AI-Powered Analysis**: Uses custom AI API to analyze context and propose solutions
- **MCP Server Integration**: Connects to Confluence and JIRA via MCP (Model Context Protocol) servers
- **Code Analysis**: Reads and analyzes Java, Python, JSON, and shell script files
- **Advanced Query Processing**: NLP-powered query analysis with intent recognition and semantic understanding

### Enterprise Features
- **High-Performance Caching**: Multi-layer caching (memory, Redis, file) with intelligent TTL management
- **Reliability & Resilience**: Circuit breaker patterns, retry logic, and fault tolerance
- **Batch Processing**: Concurrent handling of multiple queries with priority queuing
- **Semantic Search**: Advanced ranking algorithms with TF-IDF and SVD-based similarity
- **Plugin Architecture**: Extensible system for custom data sources and processors
- **Comprehensive Monitoring**: Structured logging, Prometheus metrics, and health checks
- **Web API**: FastAPI-based REST API with async support and OpenAPI documentation
- **Configuration Validation**: Automated environment and dependency validation

## Requirements

- Python 3.12 (exactly)
- Access tokens for Confluence and JIRA
- Custom AI API key
- Running MCP servers for Confluence and JIRA

## Installation

1. Clone or download the project files
2. Install dependencies:
```bash
# Using pip with requirements.txt
pip install -r requirements.txt

# OR using the modern approach with pyproject.toml
pip install -e .
```

3. Copy the environment configuration:
```bash
cp .env.example .env
```

4. Edit `.env` file with your configuration:
```env
# Custom AI API Configuration
CUSTOM_AI_API_URL=https://api.example.com/v1/chat/completions
CUSTOM_AI_API_KEY=your_custom_ai_api_key_here

# Confluence Configuration
CONFLUENCE_ACCESS_TOKEN=your_confluence_access_token_here
CONFLUENCE_BASE_URL=https://your-domain.atlassian.net/wiki

# JIRA Configuration
JIRA_ACCESS_TOKEN=your_jira_access_token_here
JIRA_BASE_URL=https://your-domain.atlassian.net

# Code Repository Configuration
CODE_REPO_PATH=./your_code_repository

# MCP Server Configuration
CONFLUENCE_MCP_SERVER_URL=ws://localhost:3001
JIRA_MCP_SERVER_URL=ws://localhost:3002
```

## Usage

### Command Line Interface

#### Basic Search
```bash
python main.py search "How to implement authentication in the API"
```

> **Note**: The project has been reorganized into functional modules. See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed information about the new organization.

#### Advanced Search Options
```bash
# Skip specific sources
python main.py search "database connection issues" --no-confluence

# Search only specific file types
python main.py search "user validation" --file-types python --file-types java

# Limit results and save to file
python main.py search "error handling" --max-results 5 --save-to results.txt

# JSON output format
python main.py search "deployment process" --output-format json
```

### Web API Interface

#### Start the Web Server
```bash
python start_api.py --host 0.0.0.0 --port 8000
```

#### API Endpoints

**Search Query**
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "authentication issues", "use_cache": true}'
```

**Batch Processing**
```bash
curl -X POST "http://localhost:8000/batch/search" \
  -H "Content-Type: application/json" \
  -d '{"queries": ["auth error", "login problem", "token validation"]}'
```

**Semantic Search**
```bash
curl -X POST "http://localhost:8000/semantic/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "authentication", "limit": 10, "min_score": 0.5}'
```

**Health Check**
```bash
curl "http://localhost:8000/health"
```

**System Metrics**
```bash
curl "http://localhost:8000/metrics"  # Prometheus format
curl "http://localhost:8000/stats"    # JSON format
```

### Get Detailed Information
```bash
# Get Confluence page details
python main.py details confluence PAGE_ID

# Get JIRA issue details  
python main.py details jira ISSUE-123

# Get code file details
python main.py details code src/main/java/App.java
```

### Repository Analysis
```bash
# Analyze current repository
python main.py analyze-repo

# Analyze specific repository
python main.py analyze-repo --repo-path /path/to/your/repo
```

### Configuration Check
```bash
python main.py config-check
```

## Architecture

The AI agent consists of several key components:

### Configuration (`config.py`)
- Manages environment variables and settings
- Uses Pydantic for validation and type safety

### AI Client (`ai_client.py`)
- Interfaces with custom AI API
- Analyzes context and generates solution proposals
- Handles API authentication and error handling

### MCP Clients (`mcp_client.py`)
- `ConfluenceMCPClient`: Searches Confluence pages and retrieves content
- `JiraMCPClient`: Searches JIRA issues and retrieves details
- WebSocket-based communication with MCP servers

### Code Reader (`code_reader.py`)
- Searches and analyzes code files (Java, Python, JSON, shell scripts)
- Pattern matching and text search capabilities
- Language-specific analysis (classes, functions, imports, etc.)

### Main Agent (`agent.py`)
- Orchestrates searches across all data sources
- Coordinates parallel data retrieval
- Manages AI analysis and solution generation

### CLI Interface (`main.py`)
- Command-line interface using Click
- Multiple output formats (text, JSON)
- Async command handling

## Authentication

The agent uses access tokens for authentication:

- **Confluence & JIRA**: Use Atlassian API tokens
  - Generate tokens at: https://id.atlassian.com/manage-profile/security/api-tokens
- **Custom AI API**: Use your custom API key
- **MCP Servers**: Tokens are passed via WebSocket headers

## Example Workflows

### 1. Troubleshooting API Issues
```bash
python main.py search "API timeout errors in user service"
```
This will:
- Search Confluence for API documentation
- Find related JIRA tickets about timeout issues  
- Examine code files in the user service
- Generate a comprehensive solution proposal

### 2. Understanding Feature Implementation
```bash
python main.py search "user authentication flow" --file-types java --file-types python
```
This will:
- Find authentication documentation in Confluence
- Look for authentication-related issues in JIRA
- Analyze Java and Python authentication code
- Provide implementation guidance

### 3. Code Review and Analysis
```bash
python main.py details code src/auth/AuthService.java
```
This will:
- Show detailed file analysis
- Extract classes, methods, and imports
- Provide code structure information

## Error Handling

The agent includes comprehensive error handling:
- Connection failures to MCP servers
- Authentication errors
- File access issues
- AI API failures
- Graceful degradation when sources are unavailable

## Extending the Agent

To add support for additional:

1. **File Types**: Update `SUPPORTED_EXTENSIONS` in `CodeRepositoryReader`
2. **Data Sources**: Create new MCP clients following the `MCPClient` pattern
3. **AI Providers**: Extend `CustomAIClient` or create new AI client classes
4. **Output Formats**: Add new formatters in `main.py`

## Performance & Optimization

### Performance Features
- **Concurrent Processing**: Parallel searches across all data sources
- **Intelligent Caching**: Multi-layer caching reduces API calls by 80%+
- **Batch Operations**: Handle multiple queries efficiently
- **Connection Pooling**: Reuse connections for better throughput
- **Async Architecture**: Non-blocking I/O throughout the system

### Monitoring & Observability
- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Metrics Collection**: Prometheus-compatible metrics
- **Health Checks**: Automated system health monitoring
- **Performance Tracking**: Request timing and success rates
- **Resource Monitoring**: CPU, memory, and disk usage tracking

### Scaling Considerations
- **Horizontal Scaling**: Stateless design supports load balancing
- **Resource Limits**: Configurable worker pools and concurrency limits
- **Cache Optimization**: Redis support for distributed caching
- **Plugin Architecture**: Extend functionality without core changes

## Troubleshooting

### Health Checks
```bash
# CLI health check
python main.py config-check

# Web API health check
curl http://localhost:8000/health

# Comprehensive system diagnostics
curl http://localhost:8000/stats
```

### Common Issues

**Connection Problems**
- Verify MCP servers are running: `netstat -an | grep 3001`
- Check network connectivity: `curl -I https://your-domain.atlassian.net`
- Validate access tokens in environment variables

**Performance Issues**
- Monitor system resources: `curl http://localhost:8000/metrics`
- Check cache hit rates in stats endpoint
- Reduce `max_results` or use specific file type filters
- Enable Redis caching for better performance

**Configuration Problems**
- Review environment variables in `.env` file
- Check file permissions for cache and log directories
- Validate URL formats and accessibility

### Debug Mode
```bash
# CLI with verbose logging
python main.py --debug search "your query"

# Web API with debug logging
python start_api.py --debug
```

### Log Analysis
```bash
# View structured logs
tail -f agent.log | jq .

# Filter error logs
grep "ERROR" agent.log | jq .

# Monitor specific component
grep "batch_processor" agent.log | jq .
```

## Testing

### Run Test Suite
```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test categories
pytest tests/test_agent.py -v
pytest tests/test_web_api.py -v
```

### Performance Testing
```bash
# Load test the web API
pip install locust

# Create load test script (examples in tests/)
locust -f tests/load_test.py --host http://localhost:8000
```

## Deployment

### Docker Deployment
```bash
# Build Docker image
docker build -t ai-agent:latest .

# Run with environment file
docker run --env-file .env -p 8000:8000 ai-agent:latest

# Docker Compose for full stack
docker-compose up -d
```

### Production Considerations
- Use environment-specific configuration files
- Set up log rotation and monitoring
- Configure load balancing and health checks
- Enable Redis for distributed caching
- Set up Prometheus monitoring and Grafana dashboards

## License

This project is provided as-is for educational and development purposes.