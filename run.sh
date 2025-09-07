#!/bin/bash
set -e  # Exit on any error

# AI Agent Run Script
# This script runs the AI Agent with proper environment setup
# Supports both local virtual environment and Docker execution

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
    echo "Usage: $0 [--docker] [COMMAND] [OPTIONS]"
    echo
    echo "Global Options:"
    echo "  --docker                   Use Docker environment (auto-detected if running in container)"
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
    echo "  $0                         # Start interactive mode (auto-detect environment)"
    echo "  $0 --docker interactive    # Start interactive mode in Docker"
    echo "  $0 search \"authentication issues\""
    echo "  $0 --docker search \"database error\" --max-results 5 --no-confluence"
    echo "  $0 api --port 8080"
    echo "  $0 config-check"
    echo "  $0 demo"
    echo
    echo "Environment:"
    if [ "$USE_DOCKER" = true ]; then
        echo "  Current mode: Docker (using $DOCKER_COMPOSE_CMD)"
    else
        echo "  Current mode: Local virtual environment"
    fi
}

# Parse global flags first
USE_DOCKER=false
DOCKER_COMPOSE_CMD="docker compose"

# Quick check for help commands before any setup
for arg in "$@"; do
    if [[ "$arg" == "help" || "$arg" == "-h" || "$arg" == "--help" ]]; then
        # Parse --docker flag to show correct help text
        for check_arg in "$@"; do
            if [[ "$check_arg" == "--docker" ]]; then
                USE_DOCKER=true
                if command -v docker-compose &> /dev/null; then
                    DOCKER_COMPOSE_CMD="docker-compose"
                elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
                    DOCKER_COMPOSE_CMD="docker compose"
                fi
                break
            fi
        done
        show_usage
        exit 0
    fi
done

# Parse remaining arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --docker)
            USE_DOCKER=true
            shift
            ;;
        *)
            break
            ;;
    esac
done

# Auto-detect Docker environment
if [ -n "$DOCKER_CONTAINER" ] || [ -f "/.dockerenv" ]; then
    USE_DOCKER=true
fi

# Check if docker-compose or docker compose is available for Docker mode
if [ "$USE_DOCKER" = true ]; then
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker-compose"
    elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker compose"
    else
        print_error "Docker mode requested but docker compose is not available"
        exit 1
    fi
fi

# Setup environment based on execution mode
if [ "$USE_DOCKER" = true ]; then
    print_step "Setting up Docker environment"
    
    # Check if docker-compose.yml exists
    if [ ! -f "docker-compose.yml" ]; then
        print_error "docker-compose.yml not found!"
        echo "Please ensure Docker setup files are present"
        exit 1
    fi
    
    # Check if .env.docker exists
    if [ ! -f ".env.docker" ]; then
        print_error ".env.docker file not found!"
        echo "Please ensure Docker environment configuration is present"
        exit 1
    fi
    
    # Ensure Docker services are running
    print_status "Checking Docker services..."
    if ! $DOCKER_COMPOSE_CMD ps ai-agent | grep -q "Up" 2>/dev/null; then
        print_status "Starting Docker services..."
        $DOCKER_COMPOSE_CMD up -d
        print_status "Waiting for services to be ready..."
        sleep 10
    else
        print_status "Docker services are already running"
    fi
    
    # Validate Docker environment
    print_step "Validating Docker configuration"
    $DOCKER_COMPOSE_CMD exec -T ai-agent python -c "
try:
    from ai_agent.core.config import load_config, validate_config
    print('✅ Docker configuration validation passed')
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
    print('You may need to check your .env.docker file settings')
"
    
else
    print_step "Setting up local virtual environment"
    
    # Check if virtual environment exists
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
fi

# Function to execute Python commands based on environment
execute_python() {
    if [ "$USE_DOCKER" = true ]; then
        $DOCKER_COMPOSE_CMD exec -T ai-agent python "$@"
    else
        python "$@"
    fi
}

# Parse command line arguments
COMMAND="${1:-interactive}"
shift || true  # Remove first argument, ignore error if no arguments

# Check if we're just showing help - no need to setup environment
if [[ "$COMMAND" == "help" || "$COMMAND" == "-h" || "$COMMAND" == "--help" ]]; then
    show_usage
    exit 0
fi

case "$COMMAND" in
    "help"|"-h"|"--help")
        # This case should not be reached due to early exit above, but kept for safety
        show_usage
        exit 0
        ;;
    
    "interactive")
        print_step "Starting AI Agent Interactive Mode"
        print_status "This will launch the guided problem-solving interface"
        echo
        if [ "$USE_DOCKER" = true ]; then
            exec $DOCKER_COMPOSE_CMD exec ai-agent python main.py interactive "$@"
        else
            exec python main.py interactive "$@"
        fi
        ;;
    
    "search")
        if [ $# -eq 0 ]; then
            print_error "Search query required"
            echo "Usage: $0 search <query> [options]"
            exit 1
        fi
        
        print_step "Running AI Agent Search"
        if [ "$USE_DOCKER" = true ]; then
            exec $DOCKER_COMPOSE_CMD exec ai-agent python main.py search "$@"
        else
            exec python main.py search "$@"
        fi
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
        if [ "$USE_DOCKER" = true ]; then
            # For Docker mode, the API server is already running as part of the container
            # Just show the user how to access it
            print_status "API server is running in Docker container"
            print_status "Access the API at: http://localhost:8000"
            print_status "To run API server interactively in Docker:"
            echo "  $DOCKER_COMPOSE_CMD exec ai-agent python start_api.py --host \"$HOST\" --port \"$PORT\" --workers \"$WORKERS\""
        else
            exec python start_api.py --host "$HOST" --port "$PORT" --workers "$WORKERS"
        fi
        ;;
    
    "config-check")
        print_step "Running Configuration Check"
        if [ "$USE_DOCKER" = true ]; then
            exec $DOCKER_COMPOSE_CMD exec ai-agent python main.py config-check
        else
            exec python main.py config-check
        fi
        ;;
    
    "health-check")
        print_step "Running Health Checks"
        if [ "$USE_DOCKER" = true ]; then
            $DOCKER_COMPOSE_CMD exec -T ai-agent python -c "
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
        else
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
        fi
        ;;
    
    "demo")
        print_step "Running Phase 1 Improvements Demo"
        if [ -f "examples/phase1_improvements_demo.py" ]; then
            if [ "$USE_DOCKER" = true ]; then
                exec $DOCKER_COMPOSE_CMD exec ai-agent python examples/phase1_improvements_demo.py
            else
                exec python examples/phase1_improvements_demo.py
            fi
        else
            print_error "Demo script not found at examples/phase1_improvements_demo.py"
            exit 1
        fi
        ;;
    
    "test")
        print_step "Running Test Suite"
        if command -v pytest &> /dev/null; then
            print_status "Running tests with pytest..."
            if [ "$USE_DOCKER" = true ]; then
                exec $DOCKER_COMPOSE_CMD exec ai-agent python -m pytest -v
            else
                exec python -m pytest -v
            fi
        else
            print_warning "pytest not available, running basic tests..."
            if [ "$USE_DOCKER" = true ]; then
                exec $DOCKER_COMPOSE_CMD exec ai-agent python -m unittest discover -s tests -v
            else
                exec python -m unittest discover -s tests -v
            fi
        fi
        ;;
    
    "analyze-repo")
        print_step "Running Repository Analysis"
        if [ "$USE_DOCKER" = true ]; then
            exec $DOCKER_COMPOSE_CMD exec ai-agent python main.py analyze-repo "$@"
        else
            exec python main.py analyze-repo "$@"
        fi
        ;;
    
    *)
        print_error "Unknown command: $COMMAND"
        echo
        show_usage
        exit 1
        ;;
esac