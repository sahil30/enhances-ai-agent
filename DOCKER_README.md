# AI Agent Docker Environment

🐳 **Complete Docker setup for AI Agent with dummy test data**

## 🚀 Quick Start

```bash
# Build and start all services
docker-compose up --build -d

# Test the environment
./docker-test.sh
```

## 📋 What's Included

### Services
- **AI Agent**: Main application container (Python 3.12)
- **Redis**: Caching and session storage
- **Mock Confluence**: Test Confluence data server (port 8001)
- **Mock JIRA**: Test JIRA data server (port 8002)

### Features
✅ **Fully containerized environment**  
✅ **Dummy configuration with test API keys**  
✅ **Mock MCP servers for testing**  
✅ **Redis caching**  
✅ **Health checks**  
✅ **Prometheus metrics endpoint**  
✅ **Python 3.12 compatible**  

## 🌐 Service Endpoints

| Service | Port | URL | Description |
|---------|------|-----|-------------|
| AI Agent API | 8000 | http://localhost:8000 | FastAPI web server |
| Prometheus Metrics | 9090 | http://localhost:9090 | Application metrics |
| Redis | 6379 | localhost:6379 | Cache storage |
| Mock Confluence | 8001 | http://localhost:8001 | Test Confluence data |
| Mock JIRA | 8002 | http://localhost:8002 | Test JIRA data |

## 🧪 Testing the Agent

### Interactive Mode
```bash
docker-compose exec ai-agent python -m ai_agent.api.cli interactive
```

### Test Configuration
```bash
docker-compose exec ai-agent python -c "
from ai_agent.core.config import load_config
config = load_config()
print(f'✅ Config loaded: {config.custom_ai_api_url}')
"
```

### Test Mock Data
```bash
# Confluence mock data
curl http://localhost:8001/search.json | jq '.results[0].title'

# JIRA mock data  
curl http://localhost:8002/search.json | jq '.issues[0].key'

# Health checks
curl http://localhost:8001/health
curl http://localhost:8002/health
```

## 📊 Mock Test Data

### Confluence Pages (3 pages)
- **Getting Started with Development**: Setup instructions and coding standards
- **API Documentation**: Authentication, rate limiting, error handling
- **Deployment Guide**: Production deployment and rollback procedures

### JIRA Issues (3 issues)
- **PROJ-123**: Implement user authentication API (In Progress)
- **DEV-456**: Database connection pool exhaustion (Critical)
- **TEST-789**: Add automated integration tests (To Do)

## ⚙️ Configuration

The Docker environment uses `.env.docker` with dummy values:

```bash
# AI API (dummy values for testing)
CUSTOM_AI_API_URL=https://api.openai.com/v1
CUSTOM_AI_API_KEY=test-api-key-dummy-value

# Cache
REDIS_URL=redis://redis:6379/0
ENABLE_FILE_CACHE=true

# API
API_HOST=0.0.0.0
API_PORT=8000

# Mock Services
CONFLUENCE_MCP_SERVER_URL=http://mock-confluence-mcp/search.json
JIRA_MCP_SERVER_URL=http://mock-jira-mcp/search.json
```

## 🔧 Development

### View Logs
```bash
docker-compose logs -f ai-agent
docker-compose logs redis
```

### Rebuild After Code Changes
```bash
docker-compose down
docker-compose up --build -d
```

### Enter Container Shell
```bash
docker-compose exec ai-agent bash
```

## 🧹 Cleanup

```bash
# Stop all services
docker-compose down

# Remove all containers and volumes
docker-compose down -v

# Remove images
docker-compose down --rmi all -v
```

## 🎯 Test Results

When running `./docker-test.sh`, you should see:

✅ **Docker Environment Test Complete!**

- ✅ Configuration loaded successfully
- ✅ AI Agent created successfully  
- ✅ Redis connection working
- ✅ Mock services responding
- ✅ Mock data accessible (3 Confluence pages, 3 JIRA issues)
- ✅ All imports working correctly

## 🔗 Next Steps

1. **Add Real API Keys**: Edit `.env.docker` with actual API keys for full functionality
2. **Configure MCP Servers**: Set up real Confluence and JIRA MCP servers
3. **Customize Mock Data**: Edit `docker/mock-confluence.json` and `docker/mock-jira.json`
4. **Production Deployment**: Use this as a base for production Docker setup

---

**Note**: This environment uses dummy API keys and mock data. For production use, replace with real configuration and remove mock services.