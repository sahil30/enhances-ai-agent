#!/bin/bash
set -e  # Exit on any error

# AI Agent Build Script
# This script sets up the complete environment for the AI Agent

echo "🚀 AI Agent Build Script"
echo "========================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "\n${BLUE}==>${NC} $1"
}

# Check Python availability - flexible for different versions
print_step "Checking Python availability"
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    print_status "Found python3 (version $PYTHON_VERSION)"
    
    # Check minimum version (Python 3.10+)
    if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"; then
        print_error "Python 3.10+ required, found Python $PYTHON_VERSION"
        echo "Please install Python 3.10 or higher"
        exit 1
    fi
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    print_status "Found python (version $PYTHON_VERSION)"
    
    if ! python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"; then
        print_error "Python 3.10+ required, found Python $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python not found. Please install Python 3.10 or higher"
    exit 1
fi

# Check Docker availability for Atlassian MCP integration
print_step "Checking Docker availability"
if command -v docker &> /dev/null; then
    if docker info &> /dev/null; then
        print_status "Docker is available and running"
        DOCKER_AVAILABLE=true
    else
        print_warning "Docker is installed but not running"
        print_warning "Atlassian MCP integration will be limited"
        DOCKER_AVAILABLE=false
    fi
else
    print_warning "Docker is not installed"
    print_warning "Atlassian MCP integration will be limited"
    DOCKER_AVAILABLE=false
fi

echo "Using Python: $PYTHON_CMD"
$PYTHON_CMD --version

# Check if pip is available
print_step "Checking pip availability"
if ! $PYTHON_CMD -m pip --version &> /dev/null; then
    print_error "pip not available for $PYTHON_CMD"
    exit 1
fi
print_status "pip is available"

# Create virtual environment
print_step "Setting up virtual environment"
VENV_DIR="venv"

if [ -d "$VENV_DIR" ]; then
    print_warning "Virtual environment already exists. Removing old one..."
    rm -rf "$VENV_DIR"
fi

print_status "Creating new virtual environment..."
$PYTHON_CMD -m venv "$VENV_DIR"

# Activate virtual environment
print_status "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Verify we're in the virtual environment
print_status "Virtual environment Python: $(which python)"
python --version

# Upgrade pip in virtual environment
print_step "Upgrading pip"
python -m pip install --upgrade pip

# Install dependencies
print_step "Installing Python dependencies"
if [ -f "requirements.txt" ]; then
    print_status "Installing from requirements.txt..."
    python -m pip install -r requirements.txt
else
    print_error "requirements.txt not found!"
    exit 1
fi

# Install the package in development mode
print_step "Installing AI Agent in development mode"
if [ -f "pyproject.toml" ]; then
    print_status "Installing from pyproject.toml..."
    python -m pip install -e .
else
    print_warning "pyproject.toml not found, skipping editable install"
fi

# Install additional development dependencies if available
if [ -f "requirements-dev.txt" ]; then
    print_step "Installing development dependencies"
    python -m pip install -r requirements-dev.txt
fi

# Download NLTK data (required for NLP processing)
print_step "Setting up NLTK data"
python -c "
import nltk
import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

print('Downloading NLTK data...')
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True) 
nltk.download('wordnet', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)
print('NLTK data download completed')
"

# Pull Docker images for Atlassian MCP integration if Docker available
if [ "$DOCKER_AVAILABLE" = true ]; then
    print_step "Setting up Atlassian MCP integration"
    print_status "Pulling mcp-atlassian Docker image..."
    if docker pull ghcr.io/sooperset/mcp-atlassian:latest; then
        print_status "✅ mcp-atlassian image pulled successfully"
    else
        print_warning "⚠️ Failed to pull mcp-atlassian image"
        print_warning "You may need to pull it manually later"
    fi
fi

# Create necessary directories
print_step "Creating necessary directories"
mkdir -p cache
mkdir -p logs
mkdir -p data
print_status "Directories created: cache/, logs/, data/"

# Set up configuration
print_step "Setting up configuration"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_warning "Created .env from .env.example template"
        print_warning "Please edit .env file with your actual configuration values"
    else
        print_warning "Creating basic .env template..."
        cat > .env << 'EOF'
# AI Agent Configuration Template
# Copy this to .env and fill in your actual values

# Custom AI API Configuration
CUSTOM_AI_API_URL=https://your-ai-api.com/v1/chat
CUSTOM_AI_API_KEY=your-api-key-here
CUSTOM_AI_MODEL=gpt-4
CUSTOM_AI_MAX_TOKENS=2000
CUSTOM_AI_TEMPERATURE=0.7

# === New Atlassian MCP Integration (Docker-based) ===
# Cloud deployment with API tokens
CONFLUENCE_URL=https://your-company.atlassian.net/wiki
CONFLUENCE_USERNAME=your.email@company.com
CONFLUENCE_API_TOKEN=your-confluence-api-token

JIRA_URL=https://your-company.atlassian.net
JIRA_USERNAME=your.email@company.com
JIRA_API_TOKEN=your-jira-api-token

# Server/Data Center deployment with Personal Access Tokens
#CONFLUENCE_URL=https://confluence.your-company.com
#CONFLUENCE_PERSONAL_TOKEN=your-confluence-pat
#CONFLUENCE_SSL_VERIFY=false

#JIRA_URL=https://jira.your-company.com
#JIRA_PERSONAL_TOKEN=your-jira-pat
#JIRA_SSL_VERIFY=false

# Optional: Filter specific spaces/projects
#CONFLUENCE_SPACES_FILTER=DEV,TEAM,DOC
#JIRA_PROJECTS_FILTER=PROJ,DEV,SUPPORT

# Optional: OAuth 2.0 configuration (Cloud only)
#ATLASSIAN_OAUTH_CLOUD_ID=your-cloud-id
#ATLASSIAN_OAUTH_CLIENT_ID=your-oauth-client-id
#ATLASSIAN_OAUTH_CLIENT_SECRET=your-oauth-client-secret
#ATLASSIAN_OAUTH_REDIRECT_URI=http://localhost:8080/callback
#ATLASSIAN_OAUTH_SCOPE=read:jira-work write:jira-work read:confluence-content.all write:confluence-content offline_access

# Optional: Server settings
#READ_ONLY_MODE=false
#ENABLED_TOOLS=confluence_search,jira_get_issue,jira_search
#MCP_VERBOSE=true

# === Legacy MCP Servers ===
# Confluence Configuration (Legacy)
CONFLUENCE_ACCESS_TOKEN=your-confluence-token
CONFLUENCE_BASE_URL=https://yourcompany.atlassian.net/wiki
CONFLUENCE_MCP_SERVER_URL=ws://localhost:3001
CONFLUENCE_ATLASSIAN_SITE_NAME=your-site
CONFLUENCE_ATLASSIAN_USER_EMAIL=your.email@company.com
CONFLUENCE_ATLASSIAN_API_TOKEN=your-confluence-token

# JIRA Configuration (Legacy)
JIRA_ACCESS_TOKEN=your-jira-token
JIRA_BASE_URL=https://yourcompany.atlassian.net
JIRA_MCP_SERVER_URL=ws://localhost:3002
JIRA_ATLASSIAN_SITE_NAME=your-site
JIRA_ATLASSIAN_USER_EMAIL=your.email@company.com
JIRA_ATLASSIAN_API_TOKEN=your-jira-token

# Code Repository Configuration
CODE_REPO_PATH=./

# Cache Configuration
REDIS_URL=redis://localhost:6379/0

# Monitoring Configuration
LOG_LEVEL=INFO
ENABLE_METRICS=true
METRICS_PORT=9090

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
EOF
        print_warning "Created basic .env template"
    fi
    print_warning "IMPORTANT: Edit .env file with your actual API keys and configuration!"
else
    print_status ".env file already exists"
fi

# Validate the installation
print_step "Validating installation"
python -c "
import sys
print(f'Python version: {sys.version_info}')

# Test key imports
try:
    import pydantic
    print(f'✅ Pydantic: {pydantic.__version__}')
except ImportError as e:
    print(f'❌ Pydantic import failed: {e}')
    sys.exit(1)

try:
    import pydantic_settings
    print('✅ Pydantic Settings: Available')
except ImportError as e:
    print(f'❌ Pydantic Settings import failed: {e}')
    sys.exit(1)

try:
    import fastapi
    print(f'✅ FastAPI: {fastapi.__version__}')
except ImportError as e:
    print(f'❌ FastAPI import failed: {e}')
    sys.exit(1)

try:
    from ai_agent.core.config import load_config
    print('✅ AI Agent core modules: Available')
except ImportError as e:
    print(f'❌ AI Agent import failed: {e}')
    print('This might be due to missing .env configuration')

# Test Atlassian MCP integration import
try:
    from ai_agent.mcp import AtlassianMCPClient, AtlassianConfig
    print('✅ Atlassian MCP integration: Available')
except ImportError as e:
    print(f'❌ Atlassian MCP integration import failed: {e}')

# Test configuration modules
try:
    import atlassian_config
    print('✅ Atlassian configuration module: Available')
except ImportError as e:
    print(f'❌ Atlassian configuration import failed: {e}')

print('✅ Installation validation completed')
"

# Run compatibility check
print_step "Running Python 3.12 compatibility check"
if [ -f "verify_python312_compatibility.py" ]; then
    python verify_python312_compatibility.py
else
    print_warning "Compatibility check script not found, skipping"
fi

# Display completion message
print_step "Build completed successfully!"
echo
print_status "✅ Virtual environment created at: $VENV_DIR"
print_status "✅ All dependencies installed"
print_status "✅ NLTK data downloaded"
print_status "✅ Directories created"
print_status "✅ Configuration template ready"
if [ "$DOCKER_AVAILABLE" = true ]; then
    print_status "✅ Docker integration ready"
    print_status "✅ mcp-atlassian image available"
fi
echo
echo -e "${GREEN}🎉 AI Agent build completed successfully!${NC}"
echo
echo "Next steps:"
echo "1. Edit .env file with your actual configuration"
if [ "$DOCKER_AVAILABLE" = true ]; then
    echo "2. Configure Atlassian MCP integration (recommended)"
    echo "3. Test the integration: ./run.sh test-atlassian"
    echo "4. Run the agent with: ./run.sh"
else
    echo "2. Install Docker for full Atlassian MCP integration"
    echo "3. Set up legacy MCP servers if needed"
    echo "4. Run the agent with: ./run.sh"
fi
echo
echo "Available commands:"
echo "  ./run.sh interactive          # Start interactive mode"
echo "  ./run.sh start-mcp            # Test MCP server connections"
echo "  ./run.sh status-mcp           # Check MCP configuration"
echo "  ./run.sh test-atlassian       # Test Atlassian integration"
echo "  ./run.sh config-check         # Validate configuration"
echo "  ./run.sh help                 # Show all commands"
echo
echo "To activate the virtual environment manually:"
echo "  source venv/bin/activate"
echo
echo "Docker integration:"
if [ "$DOCKER_AVAILABLE" = true ]; then
    echo "  ✅ Docker available - Atlassian MCP integration ready"
    echo "  mcp-atlassian image: ghcr.io/sooperset/mcp-atlassian:latest"
else
    echo "  ⚠️ Docker not available - install for full integration"
    echo "  Install: https://www.docker.com/"
fi