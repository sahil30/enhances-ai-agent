# 🚀 AI Agent API - Postman Collection Quick Start

## 📦 What's Included

- **AI_Agent_API.postman_collection.json** - Complete API collection
- **AI_Agent_Environments.postman_environment.json** - Environment variables
- **POSTMAN_COLLECTION_GUIDE.md** - Detailed documentation
- **test_api_endpoints.sh** - Command-line testing script

## ⚡ Quick Setup (60 seconds)

### 1. Start AI Agent
```bash
./run_docker.sh start-simple
# Wait for: "Container started successfully"
```

### 2. Import to Postman
1. Open Postman
2. Click **Import** → **Upload Files**
3. Select both JSON files
4. Choose **AI Agent Environments** from environment dropdown

### 3. Test Connection
Run **Health Check** request - should return:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "services": { "agent": true, "cache": true, "batch_processor": true }
  }
}
```

## 📚 Collection Overview

### ✅ **Working Endpoints** (Ready to Test)
| Folder | Endpoint | Method | Description |
|--------|----------|---------|-------------|
| Health & Status | `/health` | GET | API health check |
| Health & Status | `/` | GET | Welcome message |
| Search & Query | `/search` | POST | Search all sources |
| Batch Operations | `/batch/search` | POST | Multiple queries |
| Batch Operations | `/batch/{id}/status` | GET | Check batch status |
| Batch Operations | `/batch/{id}/results` | GET | Get batch results |
| Semantic Search | `/semantic/search` | POST | Vector similarity search |
| Semantic Search | `/semantic/build-index` | POST | Build search index |
| Semantic Search | `/semantic/stats` | GET | Index statistics |
| Plugin System | `/plugins` | GET | List plugins |
| Plugin System | `/plugins/action` | POST | Execute plugin |
| Monitoring | `/metrics` | GET | Prometheus metrics |
| Monitoring | `/stats` | GET | Performance stats |
| Documentation | `/docs` | GET | Swagger UI |
| Documentation | `/openapi.json` | GET | API schema |

## 🎯 Essential Test Flow

### 1. Connectivity Test
```
Health Check → API Root → Get Plugins
```

### 2. Search Test
```
Basic Search → Semantic Search → Get Semantic Stats
```

### 3. Batch Processing Test  
```
Submit Batch Search → Check Batch Status → Get Batch Results
```

### 4. Monitoring Test
```
Get Metrics → Get Performance Stats
```

## 📝 Sample Requests

### Basic Search
```json
POST /search
{
  "query": "authentication implementation",
  "use_cache": true
}
```

### Semantic Search
```json  
POST /semantic/search
{
  "query": "security vulnerabilities",
  "options": {
    "max_results": 10,
    "similarity_threshold": 0.5
  }
}
```

### Batch Search
```json
POST /batch/search
{
  "queries": [
    "API rate limiting",
    "database optimization", 
    "error handling"
  ],
  "batch_options": {
    "parallel_processing": true,
    "max_results_per_query": 10
  }
}
```

## 🔧 Environment Variables

| Variable | Default | Usage |
|----------|---------|--------|
| `base_url` | `http://localhost:8000` | API endpoint |
| `batch_id` | `example-batch-id` | For batch operations |

## ⚠️ Expected Responses

### ✅ Success Responses
- **2xx status codes** - Request successful
- **JSON format** with `success: true`
- **Response time** < 30 seconds

### ⚠️ Expected Warnings  
- **Search endpoints** may return `500` with test credentials (normal)
- **Empty results** are normal without real Confluence/JIRA data

### ❌ Error Indicators
- **Connection refused** - AI Agent not running
- **404 errors** - Endpoint not available
- **Timeout** - Server overloaded

## 🐛 Troubleshooting

### AI Agent Not Responding
```bash
# Check container status
./run_docker.sh status

# Restart if needed  
./run_docker.sh stop && ./run_docker.sh start-simple

# Check logs
docker logs ai-agent-container
```

### Test All Endpoints
```bash
# Run automated tests
./test_api_endpoints.sh
```

### View API Documentation
Open browser: http://localhost:8000/docs

## 🌐 URLs for Different Deployments

| Environment | Base URL | Usage |
|-------------|----------|--------|
| **Local Docker** | `http://localhost:8000` | Development/testing |
| **Docker Compose** | `http://localhost:8000` | Full stack with monitoring |
| **Production** | `https://your-domain.com` | Live deployment |

## 📊 Monitoring Integration

The collection includes endpoints for:
- **Prometheus Metrics** - `/metrics`
- **Performance Stats** - `/stats` 
- **Health Monitoring** - `/health`
- **Plugin Status** - `/plugins`

## 🎉 Success Criteria

After importing and testing, you should be able to:
- ✅ Get healthy status from `/health`
- ✅ Search using `/search` (even with test data)
- ✅ Access Swagger docs at `/docs`
- ✅ View metrics at `/metrics`
- ✅ List plugins at `/plugins`

## 📞 Support

- **Full Documentation**: POSTMAN_COLLECTION_GUIDE.md
- **API Schema**: http://localhost:8000/docs
- **Test Script**: `./test_api_endpoints.sh`

Happy API testing! 🎯