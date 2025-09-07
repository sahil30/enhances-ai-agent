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

# Function to load .env file
load_env_file() {
    if [ -f ".env" ]; then
        # Load .env file while handling complex values properly
        while IFS='=' read -r key value; do
            # Skip empty lines and comments
            [[ -z "$key" || "$key" =~ ^[[:space:]]*# ]] && continue
            
            # Remove leading/trailing whitespace
            key=$(echo "$key" | xargs)
            value=$(echo "$value" | xargs)
            
            # Skip lines that don't have = or have invalid variable names
            [[ ! "$key" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]] && continue
            [[ -z "$value" ]] && continue
            
            # Remove quotes if present
            if [[ "$value" =~ ^\".*\"$ || "$value" =~ ^\'.*\'$ ]]; then
                value="${value:1:-1}"
            fi
            
            # Export the variable
            export "$key=$value"
        done < <(grep -v '^[[:space:]]*#' .env | grep -v '^[[:space:]]*$' | grep '=')
    fi
}

# Function to start MCP servers
start_mcp_servers() {
    print_step "Starting MCP Servers"
    
    # Load environment variables
    load_env_file
    
    # Check Confluence MCP server configuration
    if [ -z "$CONFLUENCE_ATLASSIAN_SITE_NAME" ] || [ -z "$CONFLUENCE_ATLASSIAN_USER_EMAIL" ] || [ -z "$CONFLUENCE_ATLASSIAN_API_TOKEN" ]; then
        print_error "Missing Confluence MCP server configuration in .env file:"
        echo "  - CONFLUENCE_ATLASSIAN_SITE_NAME"
        echo "  - CONFLUENCE_ATLASSIAN_USER_EMAIL" 
        echo "  - CONFLUENCE_ATLASSIAN_API_TOKEN"
        CONFLUENCE_MISSING=true
    else
        CONFLUENCE_MISSING=false
    fi
    
    # Check JIRA MCP server configuration
    if [ -z "$JIRA_ATLASSIAN_SITE_NAME" ] || [ -z "$JIRA_ATLASSIAN_USER_EMAIL" ] || [ -z "$JIRA_ATLASSIAN_API_TOKEN" ]; then
        print_error "Missing JIRA MCP server configuration in .env file:"
        echo "  - JIRA_ATLASSIAN_SITE_NAME"
        echo "  - JIRA_ATLASSIAN_USER_EMAIL" 
        echo "  - JIRA_ATLASSIAN_API_TOKEN"
        JIRA_MISSING=true
    else
        JIRA_MISSING=false
    fi
    
    if [ "$CONFLUENCE_MISSING" = true ] && [ "$JIRA_MISSING" = true ]; then
        echo ""
        print_error "No MCP server configuration found. Please update your .env file."
        echo "Note: Since your company has separate JIRA and Confluence endpoints,"
        echo "      you need separate configuration for each service."
        exit 1
    fi
    
    # Test Confluence MCP Server if configured
    if [ "$CONFLUENCE_MISSING" = false ]; then
        print_status "Testing Confluence MCP Server connection..."
        ATLASSIAN_SITE_NAME="$CONFLUENCE_ATLASSIAN_SITE_NAME" \
        ATLASSIAN_USER_EMAIL="$CONFLUENCE_ATLASSIAN_USER_EMAIL" \
        ATLASSIAN_API_TOKEN="$CONFLUENCE_ATLASSIAN_API_TOKEN" \
        npx -y @aashari/mcp-server-atlassian-confluence ls-spaces --limit 1 > confluence-mcp-test.log 2>&1
        if [ $? -eq 0 ]; then
            print_status "  ✅ Confluence MCP Server: Connection successful"
            echo "confluence_ready" > confluence-mcp.status
        else
            print_error "  ❌ Confluence MCP Server: Connection failed"
            print_warning "     Check confluence-mcp-test.log for details"
        fi
    else
        print_warning "Skipping Confluence MCP Server - configuration missing"
    fi
    
    # Test JIRA MCP Server if configured  
    if [ "$JIRA_MISSING" = false ]; then
        print_status "Testing JIRA MCP Server connection..."
        ATLASSIAN_SITE_NAME="$JIRA_ATLASSIAN_SITE_NAME" \
        ATLASSIAN_USER_EMAIL="$JIRA_ATLASSIAN_USER_EMAIL" \
        ATLASSIAN_API_TOKEN="$JIRA_ATLASSIAN_API_TOKEN" \
        npx -y @aashari/mcp-server-atlassian-jira ls-projects --limit 1 > jira-mcp-test.log 2>&1
        if [ $? -eq 0 ]; then
            print_status "  ✅ JIRA MCP Server: Connection successful"
            echo "jira_ready" > jira-mcp.status
        else
            print_error "  ❌ JIRA MCP Server: Connection failed"
            print_warning "     Check jira-mcp-test.log for details"
        fi
    else
        print_warning "Skipping JIRA MCP Server - configuration missing"
    fi
    
    print_status "MCP Server validation completed!"
    if [ -f "confluence-mcp.status" ]; then
        print_status "  - Confluence: Ready for MCP connections"
    fi
    if [ -f "jira-mcp.status" ]; then
        print_status "  - JIRA: Ready for MCP connections"
    fi
    
    echo ""
    print_status "Note: These MCP servers use STDIO transport, not WebSocket."
    print_status "Your AI agent should connect using the MCP protocol."
}

# Function to clean MCP server status
stop_mcp_servers() {
    print_step "Cleaning MCP Server Status"
    
    # Clean Confluence MCP server status
    if [ -f "confluence-mcp.status" ]; then
        rm -f confluence-mcp.status
        print_status "Cleared Confluence MCP Server status"
    else
        print_warning "No Confluence MCP Server status found"
    fi
    
    # Clean JIRA MCP server status
    if [ -f "jira-mcp.status" ]; then
        rm -f jira-mcp.status
        print_status "Cleared JIRA MCP Server status"
    else
        print_warning "No JIRA MCP Server status found"
    fi
    
    # Clean test logs
    rm -f confluence-mcp-test.log jira-mcp-test.log
    print_status "Cleaned test log files"
}

# Function to check MCP server status
check_mcp_status() {
    print_step "Checking MCP Server Configuration & Connectivity"
    
    # Load environment variables
    load_env_file
    
    # Check Confluence MCP server
    if [ -f "confluence-mcp.status" ]; then
        print_status "Confluence MCP Server: CONFIGURED & TESTED"
    else
        if [ -n "$CONFLUENCE_ATLASSIAN_SITE_NAME" ] && [ -n "$CONFLUENCE_ATLASSIAN_USER_EMAIL" ] && [ -n "$CONFLUENCE_ATLASSIAN_API_TOKEN" ]; then
            print_warning "Confluence MCP Server: CONFIGURED (not tested yet)"
        else
            print_error "Confluence MCP Server: NOT CONFIGURED"
        fi
    fi
    
    # Check JIRA MCP server
    if [ -f "jira-mcp.status" ]; then
        print_status "JIRA MCP Server: CONFIGURED & TESTED"
    else
        if [ -n "$JIRA_ATLASSIAN_SITE_NAME" ] && [ -n "$JIRA_ATLASSIAN_USER_EMAIL" ] && [ -n "$JIRA_ATLASSIAN_API_TOKEN" ]; then
            print_warning "JIRA MCP Server: CONFIGURED (not tested yet)"
        else
            print_error "JIRA MCP Server: NOT CONFIGURED"
        fi
    fi
    
    echo ""
    print_status "MCP Server Type: STDIO-based (not WebSocket)"
    print_status "To test connections, run: ./run.sh start-mcp"
    
    # Show recent test logs if available
    if [ -f "confluence-mcp-test.log" ]; then
        print_status "Recent Confluence test log available: confluence-mcp-test.log"
    fi
    
    if [ -f "jira-mcp-test.log" ]; then
        print_status "Recent JIRA test log available: jira-mcp-test.log"
    fi
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
    echo "  start-mcp                  Test MCP server connections (Confluence & JIRA)"
    echo "  stop-mcp                   Clean MCP server status/logs"
    echo "  status-mcp                 Check MCP server configuration & status"
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
    echo "  $0 start-mcp               # Test MCP server connections"
    echo "  $0 status-mcp              # Check MCP configuration status"
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
    
    "start-mcp")
        start_mcp_servers
        ;;
    
    "stop-mcp")
        stop_mcp_servers
        ;;
    
    "status-mcp")
        check_mcp_status
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