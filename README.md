# AI Agent with Integrated MCP-Atlassian

An enterprise-grade intelligent AI agent that searches across Confluence documentation, JIRA issues, and code repositories to provide comprehensive solution proposals based on user queries.

## ✨ Features

- **🔍 Multi-Source Search**: Confluence, JIRA, and code repository integration
- **🧠 AI-Powered Analysis**: Intelligent problem analysis and solution generation  
- **📦 Integrated MCP**: Built-in Atlassian connectivity (no external servers needed)
- **🌐 REST API**: Full web API with interactive interface
- **🐳 Docker Ready**: Complete containerized deployment
- **📊 Monitoring**: Prometheus metrics and health checks
- **⚡ High Performance**: Multi-layer caching and concurrent processing
- **🔧 Enterprise Ready**: Circuit breakers, retry logic, and fault tolerance

## 🚀 Quick Start

```bash
# 1. Setup
./build.sh

# 2. Configure
cp .env.example .env
# Edit .env with your Atlassian credentials

# 3. Run
./run.sh
```

## 📖 Documentation

- **[SETUP_GUIDE.md](./SETUP_GUIDE.md)** - Complete setup and configuration guide
- **[PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)** - Codebase organization and architecture
- **[PHASE1_IMPROVEMENTS.md](./PHASE1_IMPROVEMENTS.md)** - Recent enhancements and features

## 🛠️ Available Commands

```bash
# Interactive mode (default)
./run.sh

# Direct search  
./run.sh search "authentication issues"

# Web API server
./run.sh api

# Health checks
./run.sh config-check
./run.sh health-check

# Docker deployment
./run_docker.sh build
./run_docker.sh start
```

## 📋 Requirements

- **Python 3.10+** (Python 3.11+ recommended)
- **Atlassian API tokens** for Confluence and JIRA access
- **Custom AI API key** (OpenAI, Azure OpenAI, etc.)
- **Docker** (optional, for containerized deployment)

## 🎯 Integration Modes

### Integrated Mode (Recommended)
```env
USE_INTEGRATED_ATLASSIAN=true
DISABLE_EXTERNAL_MCP=true
```
- Built-in Atlassian connectivity
- No external server dependencies
- Faster startup and response times

### External MCP Server Mode
```env
USE_INTEGRATED_ATLASSIAN=false
CONFLUENCE_MCP_SERVER_URL=ws://localhost:3001
JIRA_MCP_SERVER_URL=ws://localhost:3002
```
- Requires separate MCP server processes
- WebSocket-based communication

## 🌐 API Endpoints

Once running, access these endpoints:

- **Health Check**: `GET http://localhost:8000/health`
- **Search**: `POST http://localhost:8000/search`
- **Interactive Query**: `POST http://localhost:8000/query`
- **Metrics**: `GET http://localhost:9090/metrics`
- **API Documentation**: `http://localhost:8000/docs`

## 🔑 Authentication

Get your Atlassian API tokens:
1. Visit: https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Add tokens to your `.env` file

## 🐳 Docker Quick Start

```bash
# Build and start with Docker Compose
./run_docker.sh build
./run_docker.sh start

# Access the application
curl http://localhost:8000/health
```

## 🔧 Troubleshooting

**Module import errors:**
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/ai_agent"
./build.sh
```

**Configuration validation errors:**
```bash
./run.sh config-check
```

**Atlassian connection issues:**
- Verify API tokens are correct
- Check base URLs format
- Enable integrated mode: `USE_INTEGRATED_ATLASSIAN=true`

## 📈 Performance Features

- **Concurrent Processing**: Parallel searches across all sources
- **Multi-layer Caching**: Memory, Redis, and file caching
- **Batch Operations**: Handle multiple queries efficiently
- **Connection Pooling**: Optimized resource usage
- **Semantic Search**: Advanced ranking with TF-IDF and SVD

## 🏗️ Architecture

- **Config Management**: Pydantic v2 with environment validation
- **AI Integration**: Custom AI client with multiple provider support
- **MCP Protocol**: Integrated and external server support
- **Code Analysis**: Multi-language repository scanning
- **Web API**: FastAPI with async support and OpenAPI docs
- **Monitoring**: Structured logging and Prometheus metrics

## 🚀 Production Deployment

- Use production-grade configuration
- Set up reverse proxy (nginx/Apache)
- Configure monitoring (Prometheus + Grafana)
- Implement log aggregation
- Enable Redis for distributed caching
- Set up load balancing for multiple instances

## 📞 Support

For issues and questions:
1. Check the [SETUP_GUIDE.md](./SETUP_GUIDE.md) troubleshooting section
2. Run `./run.sh config-check` for validation
3. Review logs in the `./logs/` directory
4. Test individual components with `./run.sh health-check`

---

**Get started in 3 commands:**
```bash
./build.sh && cp .env.example .env && ./run.sh
```

*Edit `.env` with your credentials before running.*