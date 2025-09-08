# AI Agent API - Postman Collection Guide

This guide explains how to use the Postman collection to test and interact with the AI Agent API.

## 📁 Files Included

1. `AI_Agent_API.postman_collection.json` - Main collection with all API endpoints
2. `AI_Agent_Environments.postman_environment.json` - Environment variables for different deployments  
3. `POSTMAN_COLLECTION_GUIDE.md` - This guide

## 🚀 Quick Start

### 1. Import Collection and Environment

1. **Open Postman**
2. **Import Collection**: 
   - Click `Import` → `Upload Files`
   - Select `AI_Agent_API.postman_collection.json`
3. **Import Environment**:
   - Click `Import` → `Upload Files` 
   - Select `AI_Agent_Environments.postman_environment.json`
4. **Select Environment**: Choose "AI Agent Environments" from the environment dropdown

### 2. Start AI Agent API

Make sure your AI Agent is running:

```bash
# Docker deployment
./run_docker.sh start-simple

# Or full stack with monitoring
./run_docker.sh start

# Or local development
./run.sh api
```

### 3. Test Basic Connectivity

1. Run **Health Check** request first to verify the API is accessible
2. Run **API Root** to confirm the service is responding correctly

## 📋 Collection Structure

### 🏥 Health & Status
- **Health Check** - Verify API health and all services
- **API Root** - Get welcome message and version info  
- **API Status** - Detailed status information

### 🔍 Search & Query  
- **Basic Search** - Simple search across all sources
- **Advanced Search with Options** - Search with filters and options
- **Confluence Only Search** - Search documentation only
- **JIRA Only Search** - Search issues and tickets only
- **Code Only Search** - Search source code repositories

### 🧠 Analysis & Insights
- **Analyze Problem** - AI-powered problem analysis
- **Get Recommendations** - Get improvement suggestions

### ⚡ Batch Operations
- **Submit Batch Query** - Process multiple queries simultaneously
- **Check Batch Status** - Monitor batch job progress
- **Get Batch Results** - Retrieve completed batch results

### 🗄️ Cache Management
- **Get Cache Stats** - View cache performance metrics
- **Clear Cache** - Clear all cached data
- **Clear Specific Cache Key** - Remove specific cache entries

### 📊 Monitoring & Metrics  
- **Get Metrics** - Prometheus metrics for monitoring
- **Get Performance Stats** - Detailed performance data
- **Get System Info** - System resource information

### ⚙️ Configuration
- **Get Configuration** - View current API settings
- **Test MCP Connections** - Verify Confluence/JIRA connectivity

## 🔧 Environment Variables

The collection uses these variables that you can customize:

| Variable | Default Value | Description |
|----------|--------------|-------------|
| `base_url` | `http://localhost:8000` | API base URL |
| `batch_id` | `example-batch-id` | Current batch job ID |
| `cache_key` | `search:authentication` | Cache key for testing |
| `api_timeout` | `30000` | Request timeout (ms) |

## 💡 Usage Examples

### Basic Search Query
```json
{
  "query": "authentication implementation",
  "use_cache": true
}
```

### Advanced Search with Options
```json
{
  "query": "API security vulnerabilities", 
  "search_options": {
    "sources": ["confluence", "jira", "code"],
    "max_results": 20,
    "include_code": true,
    "include_comments": false
  },
  "use_cache": true
}
```

### Problem Analysis
```json
{
  "problem_description": "Users are experiencing slow response times in the authentication service",
  "context": {
    "system": "authentication service",
    "urgency": "high", 
    "environment": "production"
  }
}
```

### Batch Query Processing
```json
{
  "queries": [
    "authentication best practices",
    "API rate limiting implementation", 
    "database connection pooling"
  ],
  "batch_options": {
    "parallel_processing": true,
    "max_results_per_query": 10
  }
}
```

## 🧪 Testing Workflow

### 1. Health Check Workflow
```
Health Check → API Root → API Status
```

### 2. Basic Search Workflow  
```
Basic Search → Check Results → Try Advanced Search
```

### 3. Problem Analysis Workflow
```
Analyze Problem → Get Recommendations → Search Related Issues
```

### 4. Batch Processing Workflow
```
Submit Batch Query → Check Batch Status → Get Batch Results
```

### 5. Performance Testing Workflow
```
Get Metrics → Get Performance Stats → Get System Info
```

## 🔍 Response Examples

### Health Check Response
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2025-09-08T12:30:00.000Z",
    "services": {
      "agent": true,
      "cache": true, 
      "batch_processor": true,
      "plugins": 0
    }
  },
  "message": "System is healthy"
}
```

### Search Response
```json
{
  "success": true,
  "data": {
    "query": "authentication implementation",
    "results": [
      {
        "source": "confluence",
        "title": "Authentication Best Practices",
        "url": "https://confluence.example.com/...",
        "excerpt": "Implementation guide for secure authentication...",
        "score": 0.95
      }
    ],
    "total_results": 15,
    "processing_time": 0.234
  }
}
```

## 🚨 Troubleshooting

### Common Issues

1. **Connection Refused**
   - Ensure AI Agent is running: `./run_docker.sh status`
   - Check port 8000 is accessible: `curl http://localhost:8000/health`

2. **500 Internal Server Error** 
   - Check API logs: `docker logs ai-agent-container`
   - Verify configuration: Run "Get Configuration" request

3. **Empty Search Results**
   - Check MCP connections: Run "Test MCP Connections"  
   - Verify credentials in .env file
   - Try with `"use_cache": false`

4. **Timeout Errors**
   - Increase timeout in environment variables
   - Check system resources: Run "Get System Info"

### Debug Steps

1. **Start with Health Check** - Always verify API is healthy first
2. **Check Configuration** - Ensure all required settings are present  
3. **Test Connections** - Verify MCP services are accessible
4. **Monitor Metrics** - Check performance and resource usage
5. **Review Logs** - Check container/application logs for errors

## 🔐 Authentication & Security

The current collection is configured for local/development testing. For production use:

1. Add authentication headers as needed
2. Update base_url to production endpoint  
3. Configure HTTPS/TLS settings
4. Add API key management
5. Set up proper CORS policies

## 📊 Monitoring Integration

The collection includes endpoints for:

- **Prometheus Metrics** - `/metrics` endpoint for monitoring
- **Health Checks** - Automated health verification  
- **Performance Stats** - Response time and resource usage
- **Cache Statistics** - Cache hit rates and performance

## 🤝 Contributing

To add new endpoints to the collection:

1. Add new request to appropriate folder
2. Include proper request body examples
3. Add response validation tests
4. Update environment variables if needed
5. Update this guide with usage examples

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review API logs for error details
3. Test with curl commands first
4. Check the main README.md for setup instructions

Happy testing! 🚀