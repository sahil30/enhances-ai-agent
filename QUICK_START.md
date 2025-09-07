# 🚀 AI Agent Quick Start Guide

This guide gets you up and running with the AI Agent in minutes!

## 📋 Prerequisites

- **Python 3.12** (exactly) - [Download here](https://www.python.org/downloads/)
- **Git** (for cloning repositories)
- **API Access**: Confluence & JIRA tokens, Custom AI API key
- **Optional**: Redis server (for advanced caching)

## ⚡ Quick Setup (2 Minutes)

### 1. Build & Install Dependencies

```bash
# Make scripts executable (if needed)
chmod +x build.sh run.sh

# Run the build script (installs everything)
./build.sh
```

**What this does:**
- ✅ Validates Python 3.12 installation
- ✅ Creates virtual environment
- ✅ Installs all dependencies
- ✅ Downloads NLTK data
- ✅ Creates configuration template
- ✅ Runs compatibility checks

### 2. Configure Your Environment

```bash
# Copy configuration template
cp .env.example .env

# Edit with your actual values
nano .env  # or vim .env, or use your favorite editor
```

**Required Configuration:**
```bash
# Your AI API (OpenAI, Anthropic, etc.)
CUSTOM_AI_API_URL=https://api.openai.com/v1/chat/completions
CUSTOM_AI_API_KEY=sk-your-api-key-here

# Confluence (get token at: https://id.atlassian.com/manage-profile/security/api-tokens)
CONFLUENCE_ACCESS_TOKEN=your-token-here
CONFLUENCE_BASE_URL=https://yourcompany.atlassian.net/wiki

# JIRA (same token as Confluence for Atlassian Cloud)
JIRA_ACCESS_TOKEN=your-token-here  
JIRA_BASE_URL=https://yourcompany.atlassian.net

# MCP Server URLs (if you have them running)
CONFLUENCE_MCP_SERVER_URL=ws://localhost:3001
JIRA_MCP_SERVER_URL=ws://localhost:3002
```

### 3. Run the Agent

```bash
# Start interactive mode (recommended for first use)
./run.sh

# Or explicitly
./run.sh interactive
```

## 🎮 Usage Examples

### Interactive Mode (Recommended)
```bash
./run.sh interactive
```
- 🎯 Guided problem-solving workflow
- 📊 Intelligent result ranking and cross-correlations
- 💡 Step-by-step solution implementation
- 🔍 Advanced search strategies based on problem type

### Direct Search
```bash
# Basic search
./run.sh search "How to implement JWT authentication in Java?"

# Advanced search with options
./run.sh search "database connection issues" \
  --max-results 10 \
  --no-confluence \
  --output-format json
```

### Web API Server
```bash
# Start API server
./run.sh api

# Custom host/port
./run.sh api --host 0.0.0.0 --port 8080 --workers 2
```

### System Operations
```bash
# Check configuration
./run.sh config-check

# Run health checks
./run.sh health-check

# Run demo of improvements
./run.sh demo

# Run tests
./run.sh test
```

## 🔧 Advanced Configuration

### Team-Specific Setup

**R&D Team Example:**
```bash
# In .env file
CONFLUENCE_SPACES=["RNDTEAM", "ARCHITECTURE", "API-DOCS"]
JIRA_PROJECTS=["RND", "PLATFORM"]
JIRA_ISSUE_KEY_PREFIXES=["RNDPLAN", "RNDDEV", "RNDTEST"]
```

**Frontend Team Example:**
```bash
CONFLUENCE_SPACES=["FRONTEND", "DESIGN", "UX"]
JIRA_PROJECTS=["UI", "WEBAPP"]
JIRA_ISSUE_KEY_PREFIXES=["FRONTEND", "UI", "UX"]
CODE_SUPPORTED_EXTENSIONS=[".js", ".ts", ".jsx", ".tsx", ".css", ".json"]
```

### Performance Tuning
```bash
# Cache settings (in seconds)
CACHE_TTL_SHORT=300      # 5 minutes
CACHE_TTL_MEDIUM=1800    # 30 minutes
CACHE_TTL_LONG=3600      # 1 hour

# Code search optimization
CODE_MAX_FILE_SIZE=1048576  # 1MB max file size
CODE_EXCLUDE_PATTERNS=["node_modules/*", "target/*", "build/*", ".git/*"]
```

## 🌐 Web API Usage

Once the API server is running (`./run.sh api`):

### Search Endpoint
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "authentication issues",
    "options": {
      "max_results": 10,
      "search_jira": true,
      "search_confluence": true,
      "search_code": true
    }
  }'
```

### Health Check
```bash
curl http://localhost:8000/health
```

### Interactive API Documentation
Visit: http://localhost:8000/docs

## 🛠️ Development Setup

### Enable Development Mode
```bash
# Install development dependencies (if available)
pip install -r requirements-dev.txt

# Run in development mode with auto-reload
./run.sh api --host localhost --port 8080 --workers 1
```

### Running Tests
```bash
# Run all tests
./run.sh test

# Run specific test
python -m pytest tests/test_agent.py -v
```

## 🚨 Troubleshooting

### Common Issues

**1. Python 3.12 Not Found**
```bash
# Check Python version
python3 --version

# If not 3.12, install Python 3.12 exactly
# macOS: brew install python@3.12
# Ubuntu: apt install python3.12
# Windows: Download from python.org
```

**2. Build Script Fails**
```bash
# Clean and retry
rm -rf venv
./build.sh
```

**3. Configuration Errors**
```bash
# Validate configuration
./run.sh config-check

# Check .env file exists and has required values
cat .env
```

**4. MCP Connection Failures**
```bash
# The agent can run without MCP servers, but with limited functionality
# Check if MCP servers are running on specified ports
curl -H "Upgrade: websocket" http://localhost:3001  # Confluence
curl -H "Upgrade: websocket" http://localhost:3002  # JIRA
```

**5. Import Errors**
```bash
# Ensure virtual environment is activated
source venv/bin/activate
python -c "import ai_agent; print('✅ Import successful')"
```

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
./run.sh search "test query"
```

### Get Help
```bash
# Show all available commands
./run.sh help

# Show build script help
./build.sh --help
```

## 🎯 What's Next?

1. **Explore Interactive Mode**: Start with `./run.sh interactive` for guided problem-solving
2. **Set Up Team Filters**: Configure `JIRA_ISSUE_KEY_PREFIXES` for your team
3. **Try Advanced Ranking**: The agent uses ML-powered relevance scoring
4. **API Integration**: Use the web API for programmatic access
5. **Monitoring**: Check out the metrics at http://localhost:9090/metrics

## 📚 Additional Resources

- **Detailed Documentation**: See `HOW_TO_RUN.md` for comprehensive setup
- **Architecture Overview**: Check `PROJECT_STRUCTURE.md`
- **Phase 1 Improvements**: Review `PHASE1_IMPROVEMENTS.md`
- **Configuration Reference**: Full options in `.env.example`

---

**🎉 You're ready to go! Start with `./run.sh interactive` for the best experience.**