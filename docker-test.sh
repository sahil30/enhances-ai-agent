#!/bin/bash
set -e

# Docker Test Script for AI Agent
echo "🐳 AI Agent Docker Test Suite"
echo "============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[TEST]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
print_info "Checking Docker availability..."
if ! docker info >/dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi
print_status "Docker is running"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose not found. Please install docker-compose."
    exit 1
fi
print_status "docker-compose is available"

# Create required directories
print_info "Creating required directories..."
mkdir -p cache logs data
print_status "Directories created"

# Build and start services
print_info "Building Docker images..."
docker-compose build --no-cache

print_info "Starting services..."
docker-compose up -d

# Wait for services to be ready
print_info "Waiting for services to start..."
sleep 10

# Test Redis connection
print_info "Testing Redis connection..."
if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
    print_status "Redis is responding"
else
    print_error "Redis is not responding"
    docker-compose logs redis
    exit 1
fi

# Test mock services
print_info "Testing mock Confluence service..."
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    print_status "Mock Confluence service is responding"
else
    print_error "Mock Confluence service is not responding"
    docker-compose logs mock-confluence-mcp
fi

print_info "Testing mock JIRA service..."
if curl -f http://localhost:8002/health > /dev/null 2>&1; then
    print_status "Mock JIRA service is responding"
else
    print_error "Mock JIRA service is not responding"
    docker-compose logs mock-jira-mcp
fi

# Test AI Agent container
print_info "Testing AI Agent container startup..."
sleep 5

if docker-compose ps ai-agent | grep -q "Up"; then
    print_status "AI Agent container is running"
else
    print_error "AI Agent container failed to start"
    docker-compose logs ai-agent
    exit 1
fi

# Test AI Agent health check
print_info "Testing AI Agent health check..."
for i in {1..6}; do
    if docker-compose exec -T ai-agent python -c "from ai_agent.core.config import load_config; print('Config loaded successfully')" 2>/dev/null; then
        print_status "AI Agent configuration is valid"
        break
    else
        print_warning "Attempt $i/6: Waiting for AI Agent to be ready..."
        sleep 5
    fi
done

# Test import functionality
print_info "Testing AI Agent imports..."
if docker-compose exec -T ai-agent python -c "
from ai_agent.core.config import load_config
from ai_agent.core.agent import AIAgent
from ai_agent.api.cli import cli
print('✅ All imports successful')
"; then
    print_status "AI Agent imports working correctly"
else
    print_error "AI Agent imports failed"
    docker-compose logs ai-agent
fi

# Test API endpoints (if available)
print_info "Testing API server startup..."
sleep 3

# Test mock data endpoints
print_info "Testing mock data retrieval..."
if curl -f http://localhost:8001/search.json > /dev/null 2>&1; then
    print_status "Mock Confluence data is accessible"
    CONFLUENCE_RESULTS=$(curl -s http://localhost:8001/search.json | jq '.results | length' 2>/dev/null || echo "0")
    print_info "Mock Confluence has $CONFLUENCE_RESULTS results"
else
    print_warning "Mock Confluence data is not accessible"
fi

if curl -f http://localhost:8002/search.json > /dev/null 2>&1; then
    print_status "Mock JIRA data is accessible" 
    JIRA_RESULTS=$(curl -s http://localhost:8002/search.json | jq '.issues | length' 2>/dev/null || echo "0")
    print_info "Mock JIRA has $JIRA_RESULTS issues"
else
    print_warning "Mock JIRA data is not accessible"
fi

# Display service status
print_info "Service Status:"
docker-compose ps

print_info "Container Logs (last 10 lines):"
echo "--- AI Agent Logs ---"
docker-compose logs --tail=10 ai-agent

echo
echo "--- Redis Logs ---"
docker-compose logs --tail=5 redis

# Final test summary
echo
print_status "🎉 Docker Environment Test Complete!"
echo
print_info "Available services:"
print_info "  • AI Agent: http://localhost:8000"
print_info "  • Prometheus Metrics: http://localhost:9090"
print_info "  • Redis: localhost:6379"
print_info "  • Mock Confluence: http://localhost:8001"
print_info "  • Mock JIRA: http://localhost:8002"
echo
print_info "To interact with the AI Agent:"
print_info "  docker-compose exec ai-agent python -m ai_agent.api.cli interactive"
echo
print_info "To stop services:"
print_info "  docker-compose down"
echo
print_info "To view logs:"
print_info "  docker-compose logs -f ai-agent"