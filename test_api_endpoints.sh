#!/bin/bash

# AI Agent API Endpoint Testing Script
# This script tests the main endpoints that are included in the Postman collection

set -e

BASE_URL="http://localhost:8000"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🚀 Testing AI Agent API Endpoints"
echo "================================="
echo "Base URL: $BASE_URL"
echo ""

# Function to test endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    
    echo -n "Testing $description... "
    
    if [ -n "$data" ]; then
        response=$(curl -s -w "%{http_code}" -X "$method" "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    else
        response=$(curl -s -w "%{http_code}" -X "$method" "$BASE_URL$endpoint")
    fi
    
    # Extract status code (last 3 characters)
    status_code="${response: -3}"
    response_body="${response%???}"
    
    if [[ "$status_code" =~ ^[2][0-9][0-9]$ ]]; then
        echo -e "${GREEN}✅ PASS${NC} ($status_code)"
    elif [[ "$status_code" =~ ^[4][0-9][0-9]$ ]]; then
        echo -e "${YELLOW}⚠️  WARN${NC} ($status_code)"
    else
        echo -e "${RED}❌ FAIL${NC} ($status_code)"
        echo "   Response: ${response_body:0:100}..."
    fi
}

echo "🏥 Health & Status Endpoints"
echo "----------------------------"
test_endpoint "GET" "/health" "" "Health Check"
test_endpoint "GET" "/" "" "API Root"
test_endpoint "GET" "/status" "" "API Status"

echo ""
echo "🔍 Search & Query Endpoints" 
echo "---------------------------"
test_endpoint "POST" "/search" '{"query": "test search", "use_cache": true}' "Basic Search"
test_endpoint "POST" "/search" '{"query": "authentication", "search_options": {"sources": ["code"], "max_results": 5}, "use_cache": false}' "Advanced Search"

echo ""
echo "🧠 Analysis Endpoints"
echo "---------------------"
test_endpoint "POST" "/analyze" '{"problem_description": "Test problem analysis", "context": {"system": "test"}}' "Analyze Problem"
test_endpoint "POST" "/recommendations" '{"query": "improve performance", "context": {"technology_stack": "Python, FastAPI"}}' "Get Recommendations"

echo ""
echo "⚡ Batch Operations"  
echo "------------------"
test_endpoint "POST" "/batch/submit" '{"queries": ["test query 1", "test query 2"], "batch_options": {"parallel_processing": true}}' "Submit Batch Query"
test_endpoint "GET" "/batch/test-batch-id/status" "" "Check Batch Status"
test_endpoint "GET" "/batch/test-batch-id/results" "" "Get Batch Results"

echo ""
echo "🗄️ Cache Management"
echo "-------------------"
test_endpoint "GET" "/cache/stats" "" "Get Cache Stats"
test_endpoint "DELETE" "/cache/test-key" "" "Clear Specific Cache Key"

echo ""
echo "📊 Monitoring & Metrics"
echo "----------------------"
test_endpoint "GET" "/metrics" "" "Get Metrics"  
test_endpoint "GET" "/stats" "" "Get Performance Stats"
test_endpoint "GET" "/system/info" "" "Get System Info"

echo ""
echo "⚙️ Configuration"
echo "----------------"
test_endpoint "GET" "/config" "" "Get Configuration"
test_endpoint "GET" "/config/test-connections" "" "Test MCP Connections"

echo ""
echo "🎯 Testing Complete!"
echo "===================="
echo ""
echo "📋 Next Steps:"
echo "1. Import the Postman collection: AI_Agent_API.postman_collection.json"
echo "2. Import the environment file: AI_Agent_Environments.postman_environment.json"  
echo "3. Select the 'AI Agent Environments' environment in Postman"
echo "4. Start testing with the Health Check request"
echo "5. Refer to POSTMAN_COLLECTION_GUIDE.md for detailed usage instructions"
echo ""
echo "🐳 Docker Status:"
docker ps --filter name=ai-agent-container --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "Docker container not found - make sure AI Agent is running"