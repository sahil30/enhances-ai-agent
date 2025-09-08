#!/bin/bash
set -e  # Exit on any error

# AI Agent Docker Run Script
# This script builds and runs the AI Agent in a containerized environment
# with all dependencies and services integrated

echo "🐳 AI Agent Docker Deployment"
echo "=============================="

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

# Configuration
DOCKER_IMAGE_NAME="ai-agent"
DOCKER_TAG="latest"
CONTAINER_NAME="ai-agent-container"
DOCKER_COMPOSE_FILE="docker-compose.yml"
DOCKERFILE="Dockerfile"

# Check if Docker is available
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        echo "Please install Docker from https://www.docker.com/"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker is not running"
        echo "Please start Docker and try again"
        exit 1
    fi
    
    print_status "Docker is available and running"
}

# Check if Docker Compose is available
check_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
        print_status "Using docker-compose"
    elif docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
        print_status "Using docker compose (plugin)"
    else
        print_warning "Docker Compose not found - using basic Docker commands"
        COMPOSE_CMD=""
        return 1
    fi
    return 0
}

# Create Dockerfile if it doesn't exist
create_dockerfile() {
    print_step "Creating Dockerfile"
    
    if [ -f "$DOCKERFILE" ]; then
        print_warning "Dockerfile already exists, backing up..."
        cp "$DOCKERFILE" "$DOCKERFILE.backup"
    fi
    
    cat > "$DOCKERFILE" << 'EOF'
# AI Agent Docker Image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Docker CLI for mcp-atlassian integration
RUN curl -fsSL https://get.docker.com -o get-docker.sh && \
    sh get-docker.sh && \
    rm get-docker.sh

# Copy requirements first for better caching
COPY requirements.txt* ./

# Install base Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi && \
    pip install --no-cache-dir python-dateutil atlassian-python-api keyring beautifulsoup4 markdownify

# Download NLTK data
RUN python -c "import nltk; \
    nltk.download('punkt', quiet=True); \
    nltk.download('stopwords', quiet=True); \
    nltk.download('wordnet', quiet=True); \
    nltk.download('averaged_perceptron_tagger', quiet=True); \
    print('NLTK data downloaded')"

# Copy application code
COPY . .

# Install the application in editable mode if pyproject.toml exists
RUN if [ -f pyproject.toml ]; then pip install --no-cache-dir -e .; fi

# Create necessary directories
RUN mkdir -p cache logs data

# Set permissions
RUN chmod +x run.sh build.sh

# Expose ports
EXPOSE 8000 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command - run directly in Docker without virtual environment
CMD ["python", "start_api.py", "--host", "0.0.0.0", "--port", "8000"]
EOF

    print_status "Dockerfile created"
}

# Create docker-compose.yml if it doesn't exist
create_docker_compose() {
    print_step "Creating docker-compose.yml"
    
    if [ -f "$DOCKER_COMPOSE_FILE" ]; then
        print_warning "docker-compose.yml already exists, backing up..."
        cp "$DOCKER_COMPOSE_FILE" "$DOCKER_COMPOSE_FILE.backup"
    fi
    
    cat > "$DOCKER_COMPOSE_FILE" << 'EOF'
version: '3.8'

services:
  ai-agent:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ai-agent-container
    ports:
      - "8000:8000"
      - "9090:9090"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock  # For mcp-atlassian integration
      - ./cache:/app/cache
      - ./logs:/app/logs
      - ./data:/app/data
      - ./.env:/app/.env
    environment:
      - LOG_LEVEL=INFO
      - ENABLE_METRICS=true
      - PYTHONPATH=/app/ai_agent
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - ai-agent-network

  # Optional: Redis for caching
  redis:
    image: redis:7-alpine
    container_name: ai-agent-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    networks:
      - ai-agent-network

  # Optional: Prometheus for monitoring
  prometheus:
    image: prom/prometheus:latest
    container_name: ai-agent-prometheus
    ports:
      - "9091:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
      - '--web.enable-lifecycle'
    restart: unless-stopped
    networks:
      - ai-agent-network

networks:
  ai-agent-network:
    driver: bridge

volumes:
  redis_data:
  prometheus_data:
EOF

    print_status "docker-compose.yml created"
}

# Create monitoring configuration
create_monitoring_config() {
    print_step "Creating monitoring configuration"
    
    mkdir -p monitoring
    
    cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'ai-agent'
    static_configs:
      - targets: ['ai-agent:9090']
    scrape_interval: 10s
    metrics_path: /metrics
    
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
EOF

    print_status "Monitoring configuration created"
}

# Create .dockerignore file
create_dockerignore() {
    print_step "Creating .dockerignore"
    
    cat > .dockerignore << 'EOF'
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Git
.git/
.gitignore

# Docker
Dockerfile
docker-compose.yml
.dockerignore

# Logs and cache
logs/
cache/
*.log

# Test files
.pytest_cache/
.coverage
htmlcov/

# Development files
.env.example
README.md
*.md
examples/
docs/

# Temporary files
*.tmp
*.temp
.tmp/
EOF

    print_status ".dockerignore created"
}

# Build Docker image
build_image() {
    print_step "Building Docker image"
    
    if [ ! -f ".env" ]; then
        print_error ".env file not found"
        echo "Please create .env file with your configuration"
        echo "Run ./build.sh first to create a template"
        exit 1
    fi
    
    print_status "Building image: $DOCKER_IMAGE_NAME:$DOCKER_TAG"
    
    if docker build -t "$DOCKER_IMAGE_NAME:$DOCKER_TAG" .; then
        print_status "✅ Docker image built successfully"
    else
        print_error "❌ Failed to build Docker image"
        exit 1
    fi
}

# Start services with Docker Compose
start_compose() {
    print_step "Starting services with Docker Compose"
    
    if [ -z "$COMPOSE_CMD" ]; then
        print_error "Docker Compose not available"
        return 1
    fi
    
    # Pull external images
    print_status "Pulling external Docker images..."
    docker pull ghcr.io/sooperset/mcp-atlassian:latest || print_warning "Failed to pull mcp-atlassian image"
    
    # Start services
    print_status "Starting all services..."
    if $COMPOSE_CMD up -d --build; then
        print_status "✅ All services started successfully"
        
        # Show running containers
        echo
        print_status "Running containers:"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        
        # Show logs
        echo
        print_status "Showing recent logs (press Ctrl+C to stop):"
        $COMPOSE_CMD logs -f --tail=20
        
    else
        print_error "❌ Failed to start services"
        return 1
    fi
}

# Start single container
start_container() {
    print_step "Starting AI Agent container"
    
    # Stop existing container if running
    if docker ps -a --format '{{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
        print_status "Stopping existing container..."
        docker stop "$CONTAINER_NAME" || true
        docker rm "$CONTAINER_NAME" || true
    fi
    
    # Start new container
    print_status "Starting new container..."
    docker run -d \
        --name "$CONTAINER_NAME" \
        -p 8000:8000 \
        -p 9090:9090 \
        -e PYTHONPATH=/app/ai_agent \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v "$(pwd)/cache:/app/cache" \
        -v "$(pwd)/logs:/app/logs" \
        -v "$(pwd)/data:/app/data" \
        -v "$(pwd)/.env:/app/.env" \
        --restart unless-stopped \
        "$DOCKER_IMAGE_NAME:$DOCKER_TAG"
    
    if [ $? -eq 0 ]; then
        print_status "✅ Container started successfully"
        print_status "Container name: $CONTAINER_NAME"
        print_status "API available at: http://localhost:8000"
        print_status "Metrics available at: http://localhost:9090"
        
        # Show logs
        echo
        print_status "Showing container logs (press Ctrl+C to stop):"
        docker logs -f "$CONTAINER_NAME"
    else
        print_error "❌ Failed to start container"
        exit 1
    fi
}

# Stop services
stop_services() {
    print_step "Stopping AI Agent services"
    
    if [ -n "$COMPOSE_CMD" ] && [ -f "$DOCKER_COMPOSE_FILE" ]; then
        print_status "Stopping Docker Compose services..."
        $COMPOSE_CMD down
    fi
    
    if docker ps --format '{{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
        print_status "Stopping standalone container..."
        docker stop "$CONTAINER_NAME"
        docker rm "$CONTAINER_NAME"
    fi
    
    print_status "✅ Services stopped"
}

# Show status
show_status() {
    print_step "AI Agent Docker Status"
    
    # Check if image exists
    if docker images --format '{{.Repository}}:{{.Tag}}' | grep -q "^$DOCKER_IMAGE_NAME:$DOCKER_TAG$"; then
        print_status "Docker image: ✅ Built"
    else
        print_warning "Docker image: ❌ Not built"
    fi
    
    # Check running containers
    if docker ps --format '{{.Names}}' | grep -q "ai-agent"; then
        print_status "Containers: ✅ Running"
        echo
        docker ps --filter "name=ai-agent" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    else
        print_warning "Containers: ❌ Not running"
    fi
    
    # Check external dependencies
    echo
    print_status "External Dependencies:"
    if docker images --format '{{.Repository}}' | grep -q "ghcr.io/sooperset/mcp-atlassian"; then
        print_status "  mcp-atlassian: ✅ Available"
    else
        print_warning "  mcp-atlassian: ❌ Not pulled"
    fi
}

# Clean up
cleanup() {
    print_step "Cleaning up Docker resources"
    
    # Stop and remove containers
    print_status "Stopping and removing containers..."
    docker ps -a --filter "name=ai-agent" -q | xargs -r docker stop
    docker ps -a --filter "name=ai-agent" -q | xargs -r docker rm
    
    # Remove images
    if [ "${1:-}" = "all" ]; then
        print_status "Removing Docker images..."
        docker images --filter "reference=$DOCKER_IMAGE_NAME" -q | xargs -r docker rmi -f
        
        # Remove volumes
        print_status "Removing Docker volumes..."
        docker volume ls --filter "name=new-agent" -q | xargs -r docker volume rm
    fi
    
    # Clean up build cache
    print_status "Cleaning build cache..."
    docker builder prune -f
    
    print_status "✅ Cleanup completed"
}

# Show usage
show_usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo
    echo "Commands:"
    echo "  build                      Build Docker image and setup"
    echo "  start                      Start AI Agent with Docker Compose"
    echo "  start-simple               Start AI Agent with basic Docker"
    echo "  stop                       Stop all AI Agent services"
    echo "  restart                    Restart all services"
    echo "  status                     Show Docker deployment status"
    echo "  logs                       Show container logs"
    echo "  shell                      Open shell in running container"
    echo "  cleanup                    Clean up containers"
    echo "  cleanup-all                Clean up containers, images, and volumes"
    echo "  help                       Show this help message"
    echo
    echo "Examples:"
    echo "  $0 build                   # Build and setup everything"
    echo "  $0 start                   # Start with Docker Compose"
    echo "  $0 start-simple            # Start single container"
    echo "  $0 logs                    # View logs"
    echo "  $0 shell                   # Debug in container"
    echo
    echo "URLs after starting:"
    echo "  AI Agent API: http://localhost:8000"
    echo "  Health Check: http://localhost:8000/health"
    echo "  Metrics: http://localhost:9090"
    echo "  Prometheus: http://localhost:9091 (with compose)"
}

# Main execution
print_step "Checking prerequisites"
check_docker

DOCKER_COMPOSE_AVAILABLE=false
if check_docker_compose; then
    DOCKER_COMPOSE_AVAILABLE=true
fi

# Parse command line arguments
COMMAND="${1:-help}"
shift || true

case "$COMMAND" in
    "build")
        create_dockerfile
        create_dockerignore
        if [ "$DOCKER_COMPOSE_AVAILABLE" = true ]; then
            create_docker_compose
            create_monitoring_config
        fi
        build_image
        
        print_step "🎉 Docker setup completed!"
        echo
        print_status "Next steps:"
        echo "1. Edit .env file with your configuration"
        if [ "$DOCKER_COMPOSE_AVAILABLE" = true ]; then
            echo "2. Start with: $0 start (full stack)"
        fi
        echo "2. Start with: $0 start-simple (basic)"
        echo "3. Check status: $0 status"
        ;;
    
    "start")
        if [ "$DOCKER_COMPOSE_AVAILABLE" = true ]; then
            start_compose
        else
            print_warning "Docker Compose not available, using simple start"
            start_container
        fi
        ;;
    
    "start-simple")
        if [ ! "$(docker images -q "$DOCKER_IMAGE_NAME:$DOCKER_TAG" 2> /dev/null)" ]; then
            print_error "Docker image not found. Run '$0 build' first"
            exit 1
        fi
        start_container
        ;;
    
    "stop")
        stop_services
        ;;
    
    "restart")
        stop_services
        sleep 2
        if [ "$DOCKER_COMPOSE_AVAILABLE" = true ] && [ -f "$DOCKER_COMPOSE_FILE" ]; then
            start_compose
        else
            start_container
        fi
        ;;
    
    "status")
        show_status
        ;;
    
    "logs")
        if docker ps --format '{{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
            docker logs -f "$CONTAINER_NAME"
        elif [ "$DOCKER_COMPOSE_AVAILABLE" = true ] && [ -f "$DOCKER_COMPOSE_FILE" ]; then
            $COMPOSE_CMD logs -f
        else
            print_error "No running containers found"
            exit 1
        fi
        ;;
    
    "shell")
        if docker ps --format '{{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
            docker exec -it "$CONTAINER_NAME" /bin/bash
        else
            print_error "Container not running. Start it first with: $0 start"
            exit 1
        fi
        ;;
    
    "cleanup")
        cleanup
        ;;
    
    "cleanup-all")
        cleanup all
        ;;
    
    "help"|"-h"|"--help")
        show_usage
        ;;
    
    *)
        print_error "Unknown command: $COMMAND"
        echo
        show_usage
        exit 1
        ;;
esac