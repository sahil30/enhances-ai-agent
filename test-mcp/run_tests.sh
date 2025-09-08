#!/bin/bash

# MCP Confluence Connectivity Test Runner
# Simple script to test if MCP server can connect to Confluence

set -e

echo "🧪 MCP Confluence Connectivity Test Runner"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if config exists
if [ ! -f "config.json" ]; then
    echo -e "${YELLOW}⚠️ Config file not found!${NC}"
    echo "Creating config.json from example..."
    
    if [ -f "config.json.example" ]; then
        cp config.json.example config.json
        echo -e "${YELLOW}📝 Please edit config.json with your Confluence credentials${NC}"
        echo "Required fields:"
        echo "  - server_url: Your Atlassian domain"
        echo "  - username: Your email"
        echo "  - api_token: Your API token"
        echo "  - space_key: Confluence space to test"
        echo ""
        echo "Run this script again after updating config.json"
        exit 1
    else
        echo -e "${RED}❌ config.json.example not found${NC}"
        exit 1
    fi
fi

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
echo "🐍 Python version: $python_version"

# Check if requirements are installed
echo "📦 Checking dependencies..."
if ! python3 -c "import requests" 2>/dev/null; then
    echo -e "${YELLOW}⚠️ Installing requests library...${NC}"
    pip3 install requests
fi

echo ""
echo "🚀 Running MCP Confluence connectivity tests..."
echo ""

# Run the test
if python3 test_mcp_confluence.py; then
    echo ""
    echo -e "${GREEN}✅ All tests completed successfully!${NC}"
    echo -e "${GREEN}🎉 Your MCP server should be able to connect to Confluence${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}❌ Some tests failed${NC}"
    echo -e "${YELLOW}💡 Check the output above for specific issues${NC}"
    echo ""
    echo "Common fixes:"
    echo "1. Verify your Confluence credentials in config.json"
    echo "2. Check your internet connection" 
    echo "3. Ensure your API token has proper permissions"
    echo "4. Verify the MCP server path is correct"
    exit 1
fi