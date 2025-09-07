#!/bin/bash
set -e  # Exit on any error

# AI Agent Run Script
# This script runs the AI Agent with proper environment setup

echo "🚀 AI Agent Run Script"
echo "======================"

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

# Function to show usage
show_usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo
    echo "Commands:"
    echo "  interactive                 Launch interactive problem-solving mode (default)"
    echo "  search <query>             Search across all sources"
    echo "  api                        Start web API server"
    echo "  config-check               Validate configuration"
    echo "  health-check               Run health checks"
    echo "  demo                       Run Phase 1 improvements demo"
    echo "  test                       Run test suite"
    echo "  help                       Show this help message"
    echo
    echo "Search Options:"
    echo "  --no-confluence            Skip Confluence search"
    echo "  --no-jira                  Skip JIRA search"
    echo "  --no-code                  Skip code search"
    echo "  --max-results <n>          Maximum results per source"
    echo "  --output-format <format>   Output format (text|json)"
    echo
    echo "API Options:"
    echo "  --host <host>              API server host (default: 0.0.0.0)"
    echo "  --port <port>              API server port (default: 8000)"
    echo "  --workers <n>              Number of worker processes (default: 4)"
    echo
    echo "Examples:"
    echo "  $0                         # Start interactive mode"
    echo "  $0 interactive             # Start interactive mode"
    echo "  $0 search \"authentication issues\""
    echo "  $0 search \"database error\" --max-results 5 --no-confluence"
    echo "  $0 api --port 8080"
    echo "  $0 config-check"
    echo "  $0 demo"
}

# Check if virtual environment exists
print_step "Checking virtual environment"
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    print_error "Virtual environment not found at $VENV_DIR"
    echo "Please run './build.sh' first to set up the environment"
    exit 1
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source "$VENV_DIR/bin/activate"
print_status "Using Python: $(which python)"

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found!"
    echo "Please create .env file with your configuration."
    echo "You can copy from .env.example if available."
    exit 1
fi

# Validate basic configuration (without failing if MCP servers are down)
print_step "Validating basic configuration"
python -c "
try:
    from ai_agent.core.config import load_config, validate_config
    print('✅ Configuration validation passed')
    config = load_config()
    warnings = validate_config(config)
    if warnings:
        print('⚠️  Configuration warnings:')
        for warning in warnings:
            print(f'   • {warning}')
    else:
        print('✅ No configuration warnings')
except Exception as e:
    print(f'⚠️  Configuration issue: {e}')
    print('You may need to check your .env file settings')
"

# Parse command line arguments
COMMAND="${1:-interactive}"
shift || true  # Remove first argument, ignore error if no arguments

case "$COMMAND" in
    "help"|"-h"|"--help")
        show_usage
        exit 0
        ;;
    
    "interactive")
        print_step "Starting AI Agent Interactive Mode"
        print_status "This will launch the guided problem-solving interface"
        echo
        exec python main.py interactive "$@"
        ;;
    
    "search")
        if [ $# -eq 0 ]; then
            print_error "Search query required"
            echo "Usage: $0 search <query> [options]"
            exit 1
        fi
        
        print_step "Running AI Agent Search"
        exec python main.py search "$@"
        ;;
    
    "api")
        print_step "Starting AI Agent Web API Server"
        
        # Parse API-specific options
        HOST="0.0.0.0"
        PORT="8000"
        WORKERS="4"
        
        while [[ $# -gt 0 ]]; do
            case $1 in
                --host)
                    HOST="$2"
                    shift 2
                    ;;
                --port)
                    PORT="$2"
                    shift 2
                    ;;
                --workers)
                    WORKERS="$2"
                    shift 2
                    ;;
                *)
                    print_error "Unknown API option: $1"
                    exit 1
                    ;;
            esac
        done
        
        print_status "Starting API server at http://$HOST:$PORT"
        print_status "Workers: $WORKERS"
        echo
        exec python start_api.py --host "$HOST" --port "$PORT" --workers "$WORKERS"
        ;;
    
    "config-check")
        print_step "Running Configuration Check"
        exec python main.py config-check
        ;;
    
    "health-check")
        print_step "Running Health Checks"
        python -c "
import asyncio
import sys
from ai_agent.core.context_managers import ManagedAIAgent

async def health_check():
    print('🏥 Running AI Agent Health Check')
    print('=' * 40)
    
    try:
        agent = ManagedAIAgent()
        health = await agent.health_check()
        
        print(f'Status: {health[\"status\"]}')
        print(f'Initialized: {health[\"initialized\"]}')
        
        if health['status'] == 'healthy':
            print('✅ AI Agent is healthy!')
            return 0
        else:
            print(f'❌ AI Agent is unhealthy: {health.get(\"error\", \"Unknown error\")}')
            return 1
            
    except Exception as e:
        print(f'❌ Health check failed: {e}')
        return 1
    finally:
        try:
            await agent.close()
        except:
            pass

exit_code = asyncio.run(health_check())
sys.exit(exit_code)
"
        ;;
    
    "demo")
        print_step "Running Phase 1 Improvements Demo"
        if [ -f "examples/phase1_improvements_demo.py" ]; then
            exec python examples/phase1_improvements_demo.py
        else
            print_error "Demo script not found at examples/phase1_improvements_demo.py"
            exit 1
        fi
        ;;
    
    "test")
        print_step "Running Test Suite"
        if command -v pytest &> /dev/null; then
            print_status "Running tests with pytest..."
            exec python -m pytest -v
        else
            print_warning "pytest not available, running basic tests..."
            exec python -m unittest discover -s tests -v
        fi
        ;;
    
    "analyze-repo")
        print_step "Running Repository Analysis"
        exec python main.py analyze-repo "$@"
        ;;
    
    *)
        print_error "Unknown command: $COMMAND"
        echo
        show_usage
        exit 1
        ;;
esac