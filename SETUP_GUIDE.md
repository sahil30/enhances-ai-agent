# AI Agent with Integrated MCP-Atlassian Setup Guide

This guide provides complete instructions for setting up and running the AI Agent with integrated Atlassian (Confluence & JIRA) support.

## 🚀 Quick Start

1. **Clone and Setup**
   ```bash
   git clone <your-repo>
   cd ai-agent
   ./build.sh
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials (see Configuration section)
   ```

3. **Run the Agent**
   ```bash
   ./run.sh
   ```

## 📋 Prerequisites

- **Python 3.10+** (Python 3.11+ recommended)
- **pip** package manager
- **Git**
- **Docker** (optional, for containerized deployment)
- **Atlassian API tokens** for Confluence and JIRA access

## 🔧 Installation

### Method 1: Automated Setup (Recommended)

Run the build script to automatically set up everything:

```bash
./build.sh
```

This will:
- Create a virtual environment
- Install all Python dependencies (including integrated mcp_atlassian)
- Download required NLTK data
- Create configuration templates
- Set up necessary directories

### Method 2: Manual Setup

If you prefer manual setup:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install python-dateutil atlassian-python-api keyring beautifulsoup4 markdownify

# Download NLTK data
python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True); nltk.download('wordnet', quiet=True); nltk.download('averaged_perceptron_tagger', quiet=True)"

# Create directories
mkdir -p cache logs data

# Copy configuration template
cp .env.example .env
```

## ⚙️ Configuration

### 1. Basic Configuration

Edit your `.env` file with the following required settings:

```env
# AI API Configuration
CUSTOM_AI_API_URL=https://api.openai.com/v1/chat/completions
CUSTOM_AI_API_KEY=your-openai-api-key-here
CUSTOM_AI_MODEL=gpt-4
CUSTOM_AI_MAX_TOKENS=2000
CUSTOM_AI_TEMPERATURE=0.7

# Atlassian Configuration
CONFLUENCE_ACCESS_TOKEN=your-confluence-api-token
CONFLUENCE_BASE_URL=https://yourcompany.atlassian.net/wiki
JIRA_ACCESS_TOKEN=your-jira-api-token  
JIRA_BASE_URL=https://yourcompany.atlassian.net

# Code Repository Configuration
CODE_REPO_PATH=./

# Logging
LOG_LEVEL=INFO
```

### 2. Integrated MCP Mode (Recommended)

For the best experience, enable integrated mode:

```env
# MCP Integration Mode
USE_INTEGRATED_ATLASSIAN=true
DISABLE_EXTERNAL_MCP=true
```

### 3. Atlassian API Tokens

To get your API tokens:

1. **Go to Atlassian Account Settings**: https://id.atlassian.com/manage-profile/security/api-tokens
2. **Click "Create API token"**
3. **Label**: "AI Agent Integration"
4. **Copy the token** and add it to your `.env` file

### 4. Optional Advanced Configuration

```env
# Cache Configuration
REDIS_URL=redis://localhost:6379/0
ENABLE_FILE_CACHE=true
FILE_CACHE_DIR=./cache

# API Server Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090

# Confluence/JIRA Filtering (Optional)
CONFLUENCE_SPACES=["TEAM", "DOC", "API"]
JIRA_PROJECTS=["PROJ", "DEV", "SUPPORT"]
```

## 🏃 Running the AI Agent

### Interactive Mode (Default)

Start the interactive problem-solving interface:

```bash
./run.sh
# or
./run.sh interactive
```

This launches a guided interface where you can:
- Search across Confluence, JIRA, and code repositories
- Get comprehensive problem analysis
- Receive step-by-step solutions

### Search Mode

Perform direct searches:

```bash
./run.sh search "authentication issues"
./run.sh search "database error" --max-results 5 --no-confluence
```

### Web API Server

Start the REST API server:

```bash
./run.sh api
# or with custom settings
./run.sh api --host 0.0.0.0 --port 8080 --workers 2
```

API endpoints:
- **Health Check**: `GET http://localhost:8000/health`
- **Search**: `POST http://localhost:8000/search`
- **Interactive Query**: `POST http://localhost:8000/query`
- **Metrics**: `GET http://localhost:9090/metrics`

## 🐳 Docker Deployment

### Quick Docker Setup

```bash
# Build Docker image and setup
./run_docker.sh build

# Start with Docker Compose (includes Redis, Prometheus)
./run_docker.sh start

# Or start simple container
./run_docker.sh start-simple
```

### Docker Compose Services

The Docker deployment includes:
- **AI Agent**: Main application container
- **Redis**: Caching layer
- **Prometheus**: Metrics collection

Access points:
- **AI Agent API**: http://localhost:8000
- **Prometheus**: http://localhost:9091
- **Redis**: localhost:6379

### Docker Management Commands

```bash
./run_docker.sh status      # Check deployment status
./run_docker.sh logs        # View container logs
./run_docker.sh shell       # Open shell in container
./run_docker.sh stop        # Stop all services
./run_docker.sh cleanup     # Clean up containers
```

## 🔍 Testing and Validation

### Configuration Check

Validate your setup:

```bash
./run.sh config-check
```

### Health Check

Test all components:

```bash
./run.sh health-check
```

### MCP Status Check

Check Atlassian integration status:

```bash
./run.sh status-mcp
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. Module Import Errors

**Error**: `No module named 'mcp_atlassian'`

**Solution**:
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH="${PYTHONPATH}:$(pwd)/ai_agent"

# Or reinstall dependencies
./build.sh
```

#### 2. Configuration Validation Errors

**Error**: `Extra inputs are not permitted`

**Solution**: Update your config schema to allow unknown fields:
```python
# In ai_agent/core/config.py, ensure:
extra='ignore'  # Allow unknown fields
```

#### 3. Atlassian Connection Issues

**Error**: Connection failures to Confluence/JIRA

**Solutions**:
- Verify API tokens are correct
- Check base URLs (should not include `/rest/api`)
- Ensure network connectivity
- Try integrated mode: `USE_INTEGRATED_ATLASSIAN=true`

#### 4. Docker Issues

**Error**: Docker build or start failures

**Solutions**:
```bash
# Check Docker status
docker info

# Rebuild image
./run_docker.sh cleanup
./run_docker.sh build

# Check logs
./run_docker.sh logs
```

### Debug Mode

Enable verbose logging:

```env
LOG_LEVEL=DEBUG
MCP_DEBUG=true
```

### Support

For issues:
1. Check the logs in `./logs/` directory
2. Run configuration validation: `./run.sh config-check`
3. Test individual components: `./run.sh health-check`

## 📚 Usage Examples

### Interactive Problem Solving

```bash
./run.sh interactive
# Follow the guided prompts to:
# 1. Describe your problem
# 2. Select search sources
# 3. Review comprehensive analysis
# 4. Get implementation steps
```

### API Usage

```bash
# Search across all sources
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "authentication error", "max_results": 10}'

# Health check
curl http://localhost:8000/health
```

### Advanced Search Options

```bash
# Search specific sources
./run.sh search "login issue" --no-jira --max-results 5

# Export results
./run.sh search "database error" --output-format json > results.json
```

## 🔧 Advanced Configuration

### Custom AI Models

Support for various AI providers:

```env
# OpenAI
CUSTOM_AI_API_URL=https://api.openai.com/v1/chat/completions
CUSTOM_AI_MODEL=gpt-4

# Azure OpenAI
CUSTOM_AI_API_URL=https://your-resource.openai.azure.com/openai/deployments/gpt-4/chat/completions?api-version=2023-05-15
CUSTOM_AI_MODEL=gpt-4

# Anthropic Claude (via proxy)
CUSTOM_AI_API_URL=https://your-proxy.com/v1/chat/completions
CUSTOM_AI_MODEL=claude-3-sonnet-20240229
```

### Performance Tuning

```env
# Increase cache TTL for better performance
CACHE_TTL_SHORT=600      # 10 minutes
CACHE_TTL_MEDIUM=3600    # 1 hour
CACHE_TTL_LONG=7200      # 2 hours

# Adjust API timeouts
CONFLUENCE_TIMEOUT=60.0
JIRA_TIMEOUT=60.0

# Increase max file size for code analysis
CODE_MAX_FILE_SIZE=2097152  # 2MB
```

### Team-Specific Configuration

```env
# Filter by specific JIRA issue prefixes
JIRA_ISSUE_KEY_PREFIXES=["TEAM", "PROJ", "BUG"]

# Limit to specific Confluence spaces
CONFLUENCE_SPACES=["TEAM-DOCS", "API-DOCS", "TROUBLESHOOTING"]

# Custom code exclusions
CODE_EXCLUDE_PATTERNS=["node_modules/*", "*.test.js", "vendor/*"]
```

## 🔄 Integration Modes

### Mode 1: Integrated MCP (Recommended)

```env
USE_INTEGRATED_ATLASSIAN=true
DISABLE_EXTERNAL_MCP=true
```

**Benefits**:
- No external server dependencies
- Faster startup and response times
- Simplified deployment
- Better error handling

### Mode 2: External MCP Servers

```env
USE_INTEGRATED_ATLASSIAN=false
DISABLE_EXTERNAL_MCP=false
CONFLUENCE_MCP_SERVER_URL=ws://localhost:3001
JIRA_MCP_SERVER_URL=ws://localhost:3002
```

**Requirements**: Separate MCP server processes running

### Mode 3: Hybrid Mode

Mix of integrated and external services based on your needs.

## 📈 Monitoring and Metrics

### Prometheus Metrics

Access metrics at: `http://localhost:9090/metrics`

Key metrics:
- Request count and latency
- Search performance
- Cache hit rates
- API response times

### Log Analysis

Logs are stored in `./logs/` directory:
- `ai_agent.log`: Main application logs
- `search.log`: Search operation logs
- `mcp.log`: MCP integration logs

### Health Monitoring

Regular health checks:
```bash
# Automated health check
./run.sh health-check

# API health endpoint
curl http://localhost:8000/health
```

## 🚀 Production Deployment

### Environment Setup

1. **Use production-ready configuration**:
   ```env
   LOG_LEVEL=WARNING
   ENABLE_METRICS=true
   API_WORKERS=8
   ```

2. **Set up reverse proxy** (nginx/Apache)

3. **Configure monitoring** (Prometheus + Grafana)

4. **Set up log aggregation** (ELK stack)

### Security Considerations

- Store API tokens securely (environment variables, secrets management)
- Use HTTPS in production
- Implement rate limiting
- Regular security updates

### Scaling

- Increase API workers: `API_WORKERS=16`
- Use external Redis cluster for caching
- Consider load balancing multiple instances

---

## 🎯 Quick Reference Commands

```bash
# Setup
./build.sh                          # Initial setup
cp .env.example .env                 # Copy configuration template

# Running
./run.sh                            # Interactive mode
./run.sh search "query"             # Direct search
./run.sh api                        # Start web server

# Docker
./run_docker.sh build               # Build Docker image
./run_docker.sh start               # Start with Docker Compose
./run_docker.sh logs                # View logs

# Maintenance
./run.sh config-check               # Validate configuration
./run.sh health-check               # System health check
./run.sh status-mcp                 # MCP integration status
```

For additional help, run: `./run.sh help`