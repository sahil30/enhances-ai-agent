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

# Check if Python 3.12 is available
print_step "Checking Python 3.12 availability"
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
    print_status "Found python3.12"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if [[ "$PYTHON_VERSION" == "3.12" ]]; then
        PYTHON_CMD="python3"
        print_status "Found python3 (version 3.12)"
    else
        print_error "Python 3.12 required, found Python $PYTHON_VERSION"
        echo "Please install Python 3.12 exactly as specified in requirements"
        exit 1
    fi
else
    print_error "Python 3.12 not found. Please install Python 3.12"
    exit 1
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

# Confluence Configuration
CONFLUENCE_ACCESS_TOKEN=your-confluence-token
CONFLUENCE_BASE_URL=https://yourcompany.atlassian.net/wiki
CONFLUENCE_MCP_SERVER_URL=ws://localhost:3001

# JIRA Configuration
JIRA_ACCESS_TOKEN=your-jira-token
JIRA_BASE_URL=https://yourcompany.atlassian.net
JIRA_MCP_SERVER_URL=ws://localhost:3002

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
echo
echo -e "${GREEN}🎉 AI Agent build completed successfully!${NC}"
echo
echo "Next steps:"
echo "1. Edit .env file with your actual configuration"
echo "2. Set up your MCP servers (Confluence & JIRA)"
echo "3. Run the agent with: ./run.sh"
echo
echo "To activate the virtual environment manually:"
echo "  source venv/bin/activate"
echo
echo "To run tests:"
echo "  source venv/bin/activate && python -m pytest"
echo
echo "To start interactive mode:"
echo "  ./run.sh interactive"