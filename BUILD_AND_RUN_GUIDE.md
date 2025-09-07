# 🛠️ AI Agent Build & Run Guide

Complete guide for building, configuring, and running the AI Agent with all dependencies.

## 📁 Files Overview

### 🔨 Build & Run Scripts
- **`build.sh`** - Comprehensive build script that sets up everything
- **`run.sh`** - Universal run script with multiple commands
- **`test-build.sh`** - Verification script to test the build
- **`.env.example`** - Configuration template

### 📚 Documentation
- **`QUICK_START.md`** - 2-minute setup guide
- **`HOW_TO_RUN.md`** - Comprehensive usage documentation
- **`PHASE1_IMPROVEMENTS.md`** - Technical improvements summary

## 🚀 Complete Setup Process

### Step 1: Build Environment
```bash
# Make scripts executable
chmod +x build.sh run.sh test-build.sh

# Run the comprehensive build process
./build.sh
```

**The build script will:**
- ✅ Verify Python 3.12 installation
- ✅ Create isolated virtual environment
- ✅ Install all Python dependencies (25+ packages)
- ✅ Download NLTK data for NLP processing
- ✅ Create necessary directories (cache/, logs/, data/)
- ✅ Set up configuration template (.env.example → .env)
- ✅ Run compatibility verification
- ✅ Test all imports and dependencies

### Step 2: Configure Environment
```bash
# Edit configuration with your actual values
nano .env  # or vim .env, code .env, etc.
```

**Required Configuration Keys:**
```bash
# AI API (OpenAI, Anthropic, Azure, etc.)
CUSTOM_AI_API_URL=https://api.openai.com/v1/chat/completions
CUSTOM_AI_API_KEY=sk-your-api-key-here

# Atlassian Cloud (get tokens at: https://id.atlassian.com/manage-profile/security/api-tokens)
CONFLUENCE_ACCESS_TOKEN=your-atlassian-token
CONFLUENCE_BASE_URL=https://yourcompany.atlassian.net/wiki
JIRA_ACCESS_TOKEN=your-atlassian-token
JIRA_BASE_URL=https://yourcompany.atlassian.net

# MCP Server URLs (if you have MCP servers running)
CONFLUENCE_MCP_SERVER_URL=ws://localhost:3001
JIRA_MCP_SERVER_URL=ws://localhost:3002
```

### Step 3: Verify Setup
```bash
# Test that everything was built correctly
./test-build.sh
```

### Step 4: Run the Agent
```bash
# Start interactive mode (recommended first run)
./run.sh interactive

# Or run other commands
./run.sh help  # See all available commands
```

## 🎮 Command Reference

### `./build.sh` - Build Environment

**What it does:**
- Checks Python 3.12 installation
- Creates virtual environment
- Installs dependencies
- Sets up configuration
- Verifies installation

**Options:**
- No options - fully automated

### `./run.sh` - Run Agent

**Available Commands:**

```bash
./run.sh interactive          # Launch guided problem-solving (default)
./run.sh search "query"       # Direct search across all sources
./run.sh api                  # Start web API server
./run.sh config-check         # Validate configuration
./run.sh health-check         # Run system health checks
./run.sh demo                 # Run Phase 1 improvements demo
./run.sh test                 # Run test suite
./run.sh help                 # Show detailed help
```

**Search Examples:**
```bash
# Basic search
./run.sh search "How to implement JWT authentication?"

# Advanced search with options
./run.sh search "database connection issues" \
  --max-results 10 \
  --no-confluence \
  --output-format json

# Team-specific search (if configured)
./run.sh search "API errors" \
  --jira-key-prefixes RNDPLAN RNDDEV \
  --confluence-spaces DEV API
```

**API Server Examples:**
```bash
# Start API server (default: 0.0.0.0:8000)
./run.sh api

# Custom configuration
./run.sh api --host localhost --port 8080 --workers 2
```

### `./test-build.sh` - Verify Build

**What it checks:**
- Virtual environment exists
- Python 3.12 is active
- All dependencies import correctly
- AI Agent modules load properly
- Directories were created
- Scripts are executable
- Configuration files exist

## 🔧 Advanced Configuration

### Environment Variables

**AI API Configuration:**
```bash
CUSTOM_AI_API_URL=https://api.openai.com/v1/chat/completions
CUSTOM_AI_API_KEY=your-key
CUSTOM_AI_MODEL=gpt-4                    # Model to use
CUSTOM_AI_MAX_TOKENS=2000               # Max response length
CUSTOM_AI_TEMPERATURE=0.7               # Response creativity (0.0-2.0)
```

**Team-Specific Filtering:**
```bash
# Confluence spaces to search (JSON array or comma-separated)
CONFLUENCE_SPACES=["DEV", "API", "DOCS"]
CONFLUENCE_SPACES=DEV,API,DOCS

# JIRA projects to search
JIRA_PROJECTS=["MYPROJ", "BUGS"]

# JIRA issue key prefixes for team isolation (VERY USEFUL!)
JIRA_ISSUE_KEY_PREFIXES=["RNDPLAN", "RNDDEV", "RNDTEST"]
```

**Code Repository Settings:**
```bash
CODE_REPO_PATH=./                       # Repository path
CODE_MAX_FILE_SIZE=1048576              # 1MB max file size
CODE_SUPPORTED_EXTENSIONS=[".java", ".py", ".js", ".ts", ".json"]
CODE_EXCLUDE_PATTERNS=["node_modules/*", "target/*", ".git/*"]
```

**Performance Tuning:**
```bash
# Cache TTL (seconds)
CACHE_TTL_SHORT=300                     # 5 minutes
CACHE_TTL_MEDIUM=1800                   # 30 minutes
CACHE_TTL_LONG=3600                     # 1 hour

# API server
API_WORKERS=4                           # Worker processes
API_PORT=8000                           # Server port
```

### Team Configuration Examples

**R&D Team:**
```bash
CONFLUENCE_SPACES=["RNDTEAM", "ARCHITECTURE", "API-DOCS"]
JIRA_PROJECTS=["RND", "PLATFORM"]
JIRA_ISSUE_KEY_PREFIXES=["RNDPLAN", "RNDDEV", "RNDTEST"]
CODE_SUPPORTED_EXTENSIONS=[".java", ".py", ".sql", ".yaml"]
```

**Frontend Team:**
```bash
CONFLUENCE_SPACES=["FRONTEND", "DESIGN", "UX"]
JIRA_PROJECTS=["UI", "WEBAPP"]
JIRA_ISSUE_KEY_PREFIXES=["FRONTEND", "UI", "UX"]
CODE_SUPPORTED_EXTENSIONS=[".js", ".ts", ".jsx", ".tsx", ".css"]
```

**DevOps Team:**
```bash
CONFLUENCE_SPACES=["DEVOPS", "INFRASTRUCTURE"]
JIRA_PROJECTS=["DEVOPS", "INFRA"]
JIRA_ISSUE_KEY_PREFIXES=["DEVOPS", "INFRA", "DEPLOY"]
CODE_SUPPORTED_EXTENSIONS=[".yaml", ".yml", ".sh", ".dockerfile"]
```

## 🌐 Web API Usage

### Start API Server
```bash
./run.sh api --port 8080
```

### API Endpoints

**Search:**
```bash
curl -X POST http://localhost:8080/search \
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

**Health Check:**
```bash
curl http://localhost:8080/health
```

**Interactive Documentation:**
- Visit: http://localhost:8080/docs

## 🧪 Development Workflow

### Development Setup
```bash
# Build for development
./build.sh

# Run tests
./run.sh test

# Run with debug logging
export LOG_LEVEL=DEBUG
./run.sh search "test query"
```

### Testing
```bash
# Run all tests
./run.sh test

# Run specific tests
source venv/bin/activate
python -m pytest tests/test_agent.py -v

# Run with coverage
python -m pytest --cov=ai_agent --cov-report=html
```

## 🚨 Troubleshooting

### Common Build Issues

**1. Python 3.12 Not Found**
```bash
# Check current Python
python3 --version

# Install Python 3.12 (macOS)
brew install python@3.12

# Install Python 3.12 (Ubuntu)
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-pip
```

**2. Virtual Environment Issues**
```bash
# Clean and rebuild
rm -rf venv
./build.sh
```

**3. Dependency Installation Failures**
```bash
# Update pip first
source venv/bin/activate
python -m pip install --upgrade pip

# Reinstall dependencies
pip install -r requirements.txt
```

### Common Runtime Issues

**1. Configuration Errors**
```bash
# Check configuration
./run.sh config-check

# Verify .env file exists and has required fields
cat .env | grep -E "(API_KEY|ACCESS_TOKEN|BASE_URL)"
```

**2. MCP Server Connection Issues**
```bash
# The agent can run without MCP servers (limited functionality)
# Check if servers are running:
curl -I http://localhost:3001  # Confluence MCP
curl -I http://localhost:3002  # JIRA MCP

# Run health check
./run.sh health-check
```

**3. Import/Module Errors**
```bash
# Ensure virtual environment is active
source venv/bin/activate

# Test imports manually
python -c "from ai_agent.core.config import load_config; print('OK')"

# Run build verification
./test-build.sh
```

### Debug Mode
```bash
# Enable verbose logging
export LOG_LEVEL=DEBUG

# Run with debug output
./run.sh search "test" 2>&1 | tee debug.log
```

## 📋 Checklist for Production Deployment

### Pre-Deployment
- [ ] Run `./build.sh` successfully
- [ ] Run `./test-build.sh` successfully  
- [ ] Configure `.env` with production values
- [ ] Test `./run.sh config-check`
- [ ] Test `./run.sh health-check`
- [ ] Set up MCP servers (if using)
- [ ] Configure Redis (if using advanced caching)

### Security Checklist
- [ ] API keys are not in version control
- [ ] Use environment-specific `.env` files
- [ ] Set up proper access controls for MCP servers
- [ ] Configure firewall rules for API ports
- [ ] Use HTTPS in production
- [ ] Rotate API tokens regularly

### Performance Checklist
- [ ] Configure team-specific filters to reduce noise
- [ ] Set appropriate cache TTL values
- [ ] Configure Redis for distributed caching
- [ ] Monitor API server resources
- [ ] Set up logging aggregation

## 📞 Getting Help

### Command Help
```bash
./run.sh help                 # Show all commands
./build.sh --help            # Build script help (if supported)
./run.sh search --help       # Search command help
```

### Verification Commands
```bash
./test-build.sh              # Verify build worked
./run.sh demo               # Run demo showcasing features
./run.sh config-check       # Validate configuration
./run.sh health-check       # System health status
```

### Documentation
- **Quick Start**: `QUICK_START.md`
- **Comprehensive Guide**: `HOW_TO_RUN.md` 
- **Architecture**: `PROJECT_STRUCTURE.md`
- **Improvements**: `PHASE1_IMPROVEMENTS.md`

---

## 🎉 Success!

If you've made it through the build process successfully, you now have:

✅ **Modern AI Agent** with Python 3.12 exact compatibility  
✅ **Comprehensive Type Safety** with full IDE support  
✅ **Automatic Resource Management** with context managers  
✅ **Production-Ready Configuration** with validation  
✅ **Multiple Interface Options** (CLI, Interactive, Web API)  
✅ **Team-Specific Filtering** for relevant results  
✅ **Advanced Ranking System** with ML-powered relevance  

**Start with: `./run.sh interactive`** for the best experience! 🚀