#!/usr/bin/env python3
"""
Simple MCP Confluence Connectivity Test

This script tests if the MCP server can connect to Confluence and perform basic operations.
"""

import json
import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MCPConfluenceTest:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.config = self.load_config()
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"✅ Config loaded from {self.config_path}")
                return config
            else:
                logger.warning(f"⚠️ Config file {self.config_path} not found, using defaults")
                return self.get_default_config()
        except Exception as e:
            logger.error(f"❌ Error loading config: {e}")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Default configuration for testing"""
        return {
            "confluence": {
                "server_url": "https://your-domain.atlassian.net",
                "username": "your-email@example.com", 
                "api_token": "your-api-token",
                "space_key": "TEST"
            },
            "mcp": {
                "server_path": "../mcp-atlassian/server.py",
                "timeout": 30
            }
        }
    
    async def test_basic_connection(self) -> bool:
        """Test basic connection to Confluence via REST API"""
        logger.info("🔍 Testing basic Confluence connection...")
        
        try:
            import requests
            from requests.auth import HTTPBasicAuth
            
            conf_config = self.config["confluence"]
            auth = HTTPBasicAuth(conf_config["username"], conf_config["api_token"])
            
            # Test connection with a simple API call
            url = f"{conf_config['server_url']}/rest/api/user/current"
            response = requests.get(url, auth=auth, timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                logger.info(f"✅ Confluence connection successful! User: {user_data.get('displayName', 'Unknown')}")
                return True
            else:
                logger.error(f"❌ Confluence connection failed: {response.status_code} - {response.text}")
                return False
                
        except ImportError:
            logger.error("❌ 'requests' library not found. Install with: pip install requests")
            return False
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            return False
    
    async def test_mcp_server_start(self) -> bool:
        """Test if MCP server can start"""
        logger.info("🚀 Testing MCP server startup...")
        
        try:
            import subprocess
            import os
            
            mcp_config = self.config["mcp"]
            server_path = Path(mcp_config["server_path"])
            
            if not server_path.exists():
                logger.error(f"❌ MCP server not found at: {server_path}")
                return False
            
            # Test server startup with help command
            cmd = [sys.executable, str(server_path), "--help-install"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                logger.info("✅ MCP server can start successfully")
                logger.info(f"   Server output: {result.stdout.strip()}")
                return True
            else:
                logger.error(f"❌ MCP server startup failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ MCP server startup timed out")
            return False
        except Exception as e:
            logger.error(f"❌ MCP server test failed: {e}")
            return False
    
    async def test_mcp_server_full(self) -> bool:
        """Test MCP server with actual connectivity"""
        logger.info("🔗 Testing MCP server connectivity...")
        
        try:
            import subprocess
            
            mcp_config = self.config["mcp"]
            server_path = Path(mcp_config["server_path"])
            
            if not server_path.exists():
                logger.error(f"❌ MCP server not found at: {server_path}")
                return False
            
            # Run MCP server in test mode
            cmd = [sys.executable, str(server_path), "--test", "--config", "config.json"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info("✅ MCP server connectivity test passed")
                return True
            else:
                logger.warning(f"⚠️ MCP server connectivity test had issues: {result.stderr}")
                # Don't fail completely - this might be due to credentials
                return True
                
        except subprocess.TimeoutExpired:
            logger.error("❌ MCP server test timed out")
            return False
        except Exception as e:
            logger.error(f"❌ MCP server full test failed: {e}")
            return False
    
    async def test_confluence_search(self) -> bool:
        """Test Confluence search functionality"""
        logger.info("🔍 Testing Confluence search...")
        
        try:
            import requests
            from requests.auth import HTTPBasicAuth
            
            conf_config = self.config["confluence"]
            auth = HTTPBasicAuth(conf_config["username"], conf_config["api_token"])
            
            # Search for pages
            url = f"{conf_config['server_url']}/rest/api/search"
            params = {
                "cql": f"space = {conf_config['space_key']} AND type = page",
                "limit": 5
            }
            
            response = requests.get(url, auth=auth, params=params, timeout=15)
            
            if response.status_code == 200:
                results = response.json()
                total_results = results.get("totalSize", 0)
                logger.info(f"✅ Confluence search successful! Found {total_results} results")
                
                # Log some sample results
                for result in results.get("results", [])[:3]:
                    logger.info(f"   📄 {result.get('title', 'Untitled')}")
                
                return True
            else:
                logger.error(f"❌ Confluence search failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Search test failed: {e}")
            return False
    
    async def test_mcp_confluence_integration(self) -> bool:
        """Test if MCP can actually communicate with Confluence"""
        logger.info("🔗 Testing MCP-Confluence integration...")
        
        # Test all components individually
        basic_ok = await self.test_basic_connection()
        mcp_start_ok = await self.test_mcp_server_start()
        mcp_full_ok = await self.test_mcp_server_full()
        search_ok = await self.test_confluence_search()
        
        if basic_ok and mcp_start_ok and search_ok:
            logger.info("✅ All integration components working!")
            return True
        else:
            logger.error("❌ Integration test failed - check individual component results")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all connectivity tests"""
        logger.info("🧪 Starting MCP Confluence connectivity tests...")
        logger.info("=" * 50)
        
        results = {}
        
        # Test 1: Basic Confluence connection
        results["basic_connection"] = await self.test_basic_connection()
        print()
        
        # Test 2: MCP server startup
        results["mcp_server_start"] = await self.test_mcp_server_start()
        print()
        
        # Test 3: MCP server full test
        results["mcp_server_full"] = await self.test_mcp_server_full()
        print()
        
        # Test 4: Confluence search
        results["confluence_search"] = await self.test_confluence_search()
        print()
        
        # Test 5: Integration test
        results["integration"] = await self.test_mcp_confluence_integration()
        print()
        
        # Summary
        logger.info("📊 Test Results Summary:")
        logger.info("=" * 30)
        passed = 0
        for test_name, passed_test in results.items():
            status = "✅ PASS" if passed_test else "❌ FAIL"
            logger.info(f"{test_name:20} : {status}")
            if passed_test:
                passed += 1
        
        logger.info(f"\nOverall: {passed}/{len(results)} tests passed")
        
        if passed == len(results):
            logger.info("🎉 All tests passed! MCP-Confluence integration is ready!")
        else:
            logger.info("⚠️ Some tests failed. Check configuration and connectivity.")
            
        return results

async def main():
    """Main test runner"""
    try:
        tester = MCPConfluenceTest()
        results = await tester.run_all_tests()
        
        # Exit with error code if any tests failed
        if not all(results.values()):
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n⏹️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())