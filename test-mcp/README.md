# MCP Confluence Connectivity Test

Complete testing module with integrated MCP server to verify Confluence and JIRA connectivity.

## Quick Start (30 seconds)

1. **Setup configuration**:
   ```bash
   cd /Users/sahil/Documents/AI/test-mcp
   cp config.json.example config.json
   # Edit config.json with your Confluence and JIRA credentials
   ```

2. **Run the test**:
   ```bash
   ./run_tests.sh
   ```

## Configuration

Edit `config.json` with your Confluence and JIRA details:

```json
{
  "confluence": {
    "server_url": "https://your-domain.atlassian.net",
    "username": "your-email@example.com", 
    "api_token": "your-api-token-here",
    "space_key": "YOUR_SPACE_KEY"
  },
  "jira": {
    "server_url": "https://your-domain.atlassian.net",
    "username": "your-email@example.com",
    "api_token": "your-api-token-here"
  },
  "mcp": {
    "server_path": "./mcp_server.py",
    "timeout": 30
  }
}
```

### Getting Confluence API Token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Create API token
3. Use your email as username and the token as password

## What it Tests

✅ **Basic Connection** - Can reach Confluence API  
✅ **Authentication** - Credentials work correctly  
✅ **MCP Server Startup** - Server can start properly  
✅ **MCP Server Full Test** - Server can connect to Confluence/JIRA
✅ **Search Functionality** - Can search for pages and issues  
✅ **Integration** - All components work together  

## Expected Output

```
🧪 Starting MCP Confluence connectivity tests...
==================================================
🔍 Testing basic Confluence connection...
✅ Confluence connection successful! User: Your Name

🚀 Testing MCP server startup...
✅ MCP server can start successfully

🔗 Testing MCP server connectivity...
✅ MCP server connectivity test passed

🔍 Testing Confluence search...  
✅ Confluence search successful! Found 15 results
   📄 Getting Started Guide
   📄 API Documentation
   📄 Development Setup

🔗 Testing MCP-Confluence integration...
✅ All integration components working!

📊 Test Results Summary:
==============================
basic_connection     : ✅ PASS
mcp_server_start     : ✅ PASS
mcp_server_full      : ✅ PASS
confluence_search    : ✅ PASS
integration          : ✅ PASS

Overall: 5/5 tests passed
🎉 All tests passed! MCP-Confluence integration is ready!
```

## Files

- `test_mcp_confluence.py` - Main test script
- `mcp_server.py` - Standalone MCP server for testing
- `config.json.example` - Configuration template  
- `run_tests.sh` - Simple test runner
- `requirements.txt` - Python dependencies (includes atlassian-python-api)

## Troubleshooting

### ❌ Connection Refused
- Check your `server_url` is correct
- Ensure internet connectivity

### ❌ Authentication Failed  
- Verify your `username` (email address)
- Check your `api_token` is valid
- Make sure API token has Confluence permissions

### ❌ No Search Results
- Verify `space_key` exists and you have access
- Check if the space has any pages

### ❌ MCP Server Not Found
- The server is now included locally as `mcp_server.py`
- Check that the file exists and is executable

### ❌ Missing Dependencies
- Run: `pip3 install -r requirements.txt`
- Ensure `atlassian-python-api` is installed

## Manual Testing

You can also run tests individually:

```bash
# Install dependencies
pip3 install -r requirements.txt

# Run full test suite
python3 test_mcp_confluence.py

# Test MCP server directly
python3 mcp_server.py --test

# Test just connectivity (curl)
curl -u "email@example.com:api-token" \
  "https://your-domain.atlassian.net/rest/api/user/current"
```

## Next Steps

Once this test passes, your MCP server should be able to:
- Connect to Confluence and JIRA
- Search for pages, issues, and content  
- Retrieve page and issue data
- Work with the AI Agent API

The included `mcp_server.py` is a standalone MCP server that can be integrated into your main AI Agent system for full functionality.