# How to Run the AI Agent System

This guide provides comprehensive instructions for setting up and running the AI Agent system that integrates with Confluence and JIRA MCP servers for intelligent code analysis and solution recommendations.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [MCP Server Setup](#mcp-server-setup)
- [Running the System](#running-the-system)
- [Usage Examples](#usage-examples)
- [Monitoring and Health Checks](#monitoring-and-health-checks)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- Python 3.8 or higher
- Redis server (for caching)
- Access to Confluence and JIRA instances
- Network connectivity to MCP servers

### Required Software
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Redis (macOS)
brew install redis

# Install Redis (Ubuntu/Debian)
sudo apt-get install redis-server

# Install Redis (CentOS/RHEL)
sudo yum install redis
```

## Installation

1. **Clone or extract the project:**
```bash
cd /path/to/ai-agent
```

2. **Create virtual environment (recommended):**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Install NLTK data (for query processing):**
```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('averaged_perceptron_tagger')"
```

## Configuration

### 1. Environment Variables

Create a `.env` file in the root directory based on `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# Custom AI API Configuration
CUSTOM_AI_API_URL=https://your-ai-api.com/v1/chat
CUSTOM_AI_API_KEY=your-api-key-here
CUSTOM_AI_MODEL=gpt-4  # or your preferred model
CUSTOM_AI_MAX_TOKENS=2000
CUSTOM_AI_TEMPERATURE=0.7

# Confluence Configuration
CONFLUENCE_ACCESS_TOKEN=your-confluence-token
CONFLUENCE_BASE_URL=https://yourcompany.atlassian.net/wiki
CONFLUENCE_MCP_SERVER_URL=ws://localhost:3001
CONFLUENCE_SPACES=["DEV", "DOC", "API"]  # Optional space filtering
CONFLUENCE_TIMEOUT=30.0
CONFLUENCE_MAX_RETRIES=3

# JIRA Configuration  
JIRA_ACCESS_TOKEN=your-jira-token
JIRA_BASE_URL=https://yourcompany.atlassian.net
JIRA_MCP_SERVER_URL=ws://localhost:3002
JIRA_PROJECTS=["PROJ", "BUG", "FEAT"]  # Optional project filtering
JIRA_TIMEOUT=30.0
JIRA_MAX_RETRIES=3

# Code Repository Configuration
CODE_REPO_PATH=./your-code-repository
CODE_SUPPORTED_EXTENSIONS=[".java", ".py", ".js", ".json", ".sh", ".yml", ".yaml"]

# Cache Configuration
REDIS_URL=redis://localhost:6379/0
CACHE_TTL_SHORT=300      # 5 minutes
CACHE_TTL_MEDIUM=1800    # 30 minutes  
CACHE_TTL_LONG=3600      # 1 hour
ENABLE_FILE_CACHE=true
FILE_CACHE_DIR=./cache

# Monitoring Configuration
LOG_LEVEL=INFO
ENABLE_METRICS=true
METRICS_PORT=9090

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
ENABLE_CORS=true
```

### 2. Generate API Tokens

**Confluence Token:**
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Create API token
3. Use your email + token for basic auth

**JIRA Token:**
1. Same process as Confluence
2. Ensure token has appropriate project permissions

## MCP Server Setup

The AI Agent requires separate MCP servers for Confluence and JIRA integration.

### 1. Confluence MCP Server

```bash
# Install and start Confluence MCP server (example using Node.js)
npm install -g @confluence/mcp-server
confluence-mcp-server --port 3001 --token YOUR_CONFLUENCE_TOKEN
```

### 2. JIRA MCP Server

```bash
# Install and start JIRA MCP server
npm install -g @jira/mcp-server  
jira-mcp-server --port 3002 --token YOUR_JIRA_TOKEN
```

### 3. Verify MCP Server Connectivity

```bash
# Test Confluence MCP server
curl -H "Upgrade: websocket" http://localhost:3001

# Test JIRA MCP server
curl -H "Upgrade: websocket" http://localhost:3002
```

## Running the System

### 1. Start Redis Server

```bash
# Start Redis
redis-server

# Verify Redis is running
redis-cli ping
# Should return: PONG
```

### 2. Health Check (Recommended)

Before running the main system, verify configuration:

```bash
python -c "from ai_agent.infrastructure.health_checks import HealthChecker; import asyncio; asyncio.run(HealthChecker().run_all_checks())"
```

### 3. Command Line Interface (CLI)

**Basic search query:**
```bash
python main.py search "how to fix authentication errors"
```

**Advanced search with options:**
```bash
python main.py search "API documentation" --max-results 5 --no-jira --no-code
```

**Analyze code repository:**
```bash
python main.py analyze-repo --repo-path ./your-code --query "authentication"
```

**Configuration check:**
```bash
python main.py config-check
```

**Health monitoring:**
```bash
python main.py health-check
```

### 4. Web API Server

**Start the API server:**
```bash
python start_api.py --host 0.0.0.0 --port 8000 --workers 4
```

**With custom configuration:**
```bash
python start_api.py --host localhost --port 8080 --workers 2 --reload
```

**Background service (production):**
```bash
nohup python start_api.py --host 0.0.0.0 --port 8000 --workers 4 > api.log 2>&1 &
```

## Usage Examples

### CLI Examples

```bash
# Search across all sources
python main.py search "database connection issues"

# Search only Confluence
python main.py search "API guide" --search-confluence-only

# Search with result limit
python main.py search "error handling" --max-results 3

# Get detailed information about a result
python main.py detail confluence 123456
python main.py detail jira PROJ-123
python main.py detail code src/main/AuthService.java
```

### Web API Examples

**Search endpoint:**
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "authentication errors",
    "options": {
      "max_results": 10,
      "search_jira": true,
      "search_confluence": true,
      "search_code": true
    }
  }'
```

**Get detailed information:**
```bash
curl http://localhost:8000/detail/confluence/123456
curl http://localhost:8000/detail/jira/PROJ-123
```

**Health check:**
```bash
curl http://localhost:8000/health
```

**Get related query suggestions:**
```bash
curl -X POST http://localhost:8000/suggest \
  -H "Content-Type: application/json" \
  -d '{
    "query": "authentication",
    "context": {...}
  }'
```

### Python API Examples

```python
import asyncio
from ai_agent import AIAgent, load_config

async def main():
    # Load configuration
    config = load_config()
    
    # Initialize agent
    agent = AIAgent(config)
    
    try:
        # Process query
        result = await agent.process_query(
            "how to fix API authentication errors",
            {
                "max_results": 5,
                "search_jira": True,
                "search_confluence": True,
                "search_code": True
            }
        )
        
        print(f"Found {result['sources']['confluence']['count']} Confluence pages")
        print(f"Found {result['sources']['jira']['count']} JIRA issues")
        print(f"Found {result['sources']['code']['count']} code files")
        print(f"Solution: {result['solution']}")
        
        # Get detailed information
        if result['sources']['confluence']['data']:
            page_id = result['sources']['confluence']['data'][0]['id']
            details = await agent.get_detailed_info('confluence', page_id)
            print(f"Page title: {details['title']}")
            
    finally:
        await agent.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## Monitoring and Health Checks

### 1. Application Metrics

**Prometheus metrics endpoint:**
```bash
curl http://localhost:9090/metrics
```

**Key metrics to monitor:**
- `ai_agent_requests_total` - Total requests processed
- `ai_agent_request_duration_seconds` - Request processing time
- `ai_agent_cache_hits_total` - Cache hit rate
- `ai_agent_mcp_connections_active` - Active MCP connections
- `ai_agent_errors_total` - Error count by type

### 2. Health Checks

**Web API health endpoint:**
```bash
curl http://localhost:8000/health
```

**CLI health check:**
```bash
python main.py health-check
```

**Expected healthy response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "checks": {
    "config": "ok",
    "redis": "ok", 
    "confluence_mcp": "ok",
    "jira_mcp": "ok",
    "code_repo": "ok"
  }
}
```

### 3. Log Analysis

**View application logs:**
```bash
tail -f ai_agent.log
```

**Search for errors:**
```bash
grep -i "error\|exception\|failed" ai_agent.log
```

**Filter by component:**
```bash
grep "mcp.confluence" ai_agent.log
grep "mcp.jira" ai_agent.log
grep "cache_manager" ai_agent.log
```

## Troubleshooting

### Common Issues

**1. MCP Connection Failed**
```
Error: Failed to connect to MCP server at ws://localhost:3001
```

**Solutions:**
- Verify MCP server is running: `curl http://localhost:3001`
- Check server logs for errors
- Verify access token configuration
- Test network connectivity

**2. Redis Connection Failed**
```
Error: Redis connection failed
```

**Solutions:**
- Start Redis server: `redis-server`
- Check Redis configuration in `.env`
- Test connection: `redis-cli ping`

**3. Authentication Issues**
```
Error: 401 Unauthorized when accessing Confluence/JIRA
```

**Solutions:**
- Verify API tokens are valid and not expired
- Check user permissions for required spaces/projects
- Test tokens with direct API calls

**4. Code Repository Access**
```
Error: Unable to read code repository
```

**Solutions:**
- Verify `CODE_REPO_PATH` exists and is readable
- Check file permissions
- Ensure supported file extensions are configured

**5. High Memory Usage**
```
Warning: High memory usage detected
```

**Solutions:**
- Adjust cache settings in `.env`
- Reduce `max_results` in queries
- Enable file-based caching
- Monitor cache hit rates

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
# Set in .env file
LOG_LEVEL=DEBUG

# Or pass as environment variable
LOG_LEVEL=DEBUG python main.py search "test query"
```

### Performance Optimization

**1. Cache Configuration:**
- Increase cache TTL for stable data
- Enable Redis persistence
- Monitor cache hit rates

**2. Connection Pooling:**
- Configure MCP connection pools
- Set appropriate timeout values
- Monitor connection counts

**3. Query Optimization:**
- Use specific search terms
- Limit result counts appropriately  
- Filter by relevant spaces/projects

## Advanced Configuration

### Plugin System

Create custom plugins for additional data sources:

```python
# ai_agent/plugins/custom_source.py
from ai_agent.plugins.plugin_system import BasePlugin

class CustomSourcePlugin(BasePlugin):
    def __init__(self, config):
        super().__init__("custom_source", config)
    
    async def search(self, query: str, limit: int = 10):
        # Implement custom search logic
        return []
```

### Custom AI Model Integration

Configure custom AI models in `.env`:

```bash
CUSTOM_AI_API_URL=https://your-custom-model.com/api
CUSTOM_AI_MODEL=your-custom-model
CUSTOM_AI_MAX_TOKENS=4000
CUSTOM_AI_TEMPERATURE=0.5
```

### Batch Processing

For processing multiple queries:

```python
from ai_agent.infrastructure.batch_processor import BatchProcessor

processor = BatchProcessor(config)
queries = ["query1", "query2", "query3"]
results = await processor.process_batch(queries)
```

---

**Support**: For issues or questions, check the logs first, then verify configuration and MCP server connectivity. The health check command is your best starting point for diagnosing problems.