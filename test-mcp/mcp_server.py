#!/usr/bin/env python3
"""
MCP Atlassian Server

A standalone MCP server for testing Confluence and JIRA connectivity.
Based on the integrated Atlassian client from the AI Agent.
"""

import asyncio
import json
import sys
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import argparse

# Try to import atlassian-python-api for direct API access
try:
    from atlassian import Confluence
    from atlassian import Jira
    ATLASSIAN_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import atlassian libraries: {e}")
    print("Install with: pip install atlassian-python-api")
    Confluence = None
    Jira = None
    ATLASSIAN_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class AtlassianConfig:
    """Configuration for Atlassian services"""
    confluence_url: Optional[str] = None
    confluence_username: Optional[str] = None  
    confluence_api_token: Optional[str] = None
    jira_url: Optional[str] = None
    jira_username: Optional[str] = None
    jira_api_token: Optional[str] = None


class MCPAtlassianServer:
    """
    MCP Atlassian Server for testing connectivity
    
    This server provides MCP-compatible interface to Confluence and JIRA
    """
    
    def __init__(self, config: AtlassianConfig):
        self.config = config
        self.confluence_client = None
        self.jira_client = None
        self._initialized = False
        
    async def initialize(self) -> bool:
        """Initialize the Atlassian clients"""
        if self._initialized:
            return True
            
        if not ATLASSIAN_AVAILABLE:
            logger.warning("atlassian-python-api library not available")
            return False
        
        try:
            # Initialize Confluence client if configured
            if self.config.confluence_url and self.config.confluence_username and self.config.confluence_api_token:
                self.confluence_client = Confluence(
                    url=self.config.confluence_url,
                    username=self.config.confluence_username,
                    password=self.config.confluence_api_token
                )
                logger.info("✅ Confluence client initialized")
            else:
                logger.warning("⚠️ Confluence configuration incomplete")
            
            # Initialize JIRA client if configured  
            if self.config.jira_url and self.config.jira_username and self.config.jira_api_token:
                self.jira_client = Jira(
                    url=self.config.jira_url,
                    username=self.config.jira_username,
                    password=self.config.jira_api_token
                )
                logger.info("✅ JIRA client initialized")
            else:
                logger.warning("⚠️ JIRA configuration incomplete")
            
            self._initialized = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Atlassian clients: {e}")
            return False
    
    async def test_confluence_connection(self) -> Dict[str, Any]:
        """Test Confluence connection"""
        if not self.confluence_client:
            return {"status": "error", "message": "Confluence client not initialized"}
            
        try:
            # Get current user info
            user = self.confluence_client.user()
            return {
                "status": "success",
                "service": "confluence",
                "user": user.get("displayName", "Unknown"),
                "message": "Connection successful"
            }
        except Exception as e:
            return {
                "status": "error", 
                "service": "confluence",
                "message": f"Connection failed: {str(e)}"
            }
    
    async def test_jira_connection(self) -> Dict[str, Any]:
        """Test JIRA connection"""
        if not self.jira_client:
            return {"status": "error", "message": "JIRA client not initialized"}
            
        try:
            # Get current user info
            user = self.jira_client.user()
            return {
                "status": "success",
                "service": "jira", 
                "user": user.get("displayName", "Unknown"),
                "message": "Connection successful"
            }
        except Exception as e:
            return {
                "status": "error",
                "service": "jira", 
                "message": f"Connection failed: {str(e)}"
            }
    
    async def search_confluence(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search Confluence pages"""
        if not self.confluence_client:
            logger.warning("Confluence client not initialized")
            return []
            
        try:
            # Use CQL search for better results
            cql = f'text ~ "{query}"'
            results = self.confluence_client.cql(cql, limit=max_results)
            
            pages = []
            for result in results.get('results', []):
                content = result.get('content', {})
                pages.append({
                    'id': content.get('id'),
                    'title': content.get('title'),
                    'url': f"{self.config.confluence_url}/spaces/{content.get('space', {}).get('key')}/pages/{content.get('id')}",
                    'space': content.get('space', {}).get('name'),
                    'type': content.get('type'),
                    'excerpt': result.get('excerpt', '')
                })
                
            logger.info(f"Found {len(pages)} Confluence results for: {query}")
            return pages
            
        except Exception as e:
            logger.error(f"Confluence search failed: {e}")
            return []
    
    async def search_jira(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search JIRA issues"""
        if not self.jira_client:
            logger.warning("JIRA client not initialized") 
            return []
            
        try:
            # Use JQL search
            jql = f'text ~ "{query}"'
            results = self.jira_client.jql(jql, limit=max_results)
            
            issues = []
            for issue in results.get('issues', []):
                fields = issue.get('fields', {})
                issues.append({
                    'key': issue.get('key'),
                    'summary': fields.get('summary'),
                    'description': fields.get('description', '')[:500] if fields.get('description') else '',
                    'status': fields.get('status', {}).get('name'),
                    'priority': fields.get('priority', {}).get('name'),
                    'assignee': fields.get('assignee', {}).get('displayName') if fields.get('assignee') else None,
                    'created': fields.get('created'),
                    'updated': fields.get('updated'),
                    'url': f"{self.config.jira_url}/browse/{issue.get('key')}"
                })
                
            logger.info(f"Found {len(issues)} JIRA results for: {query}")
            return issues
            
        except Exception as e:
            logger.error(f"JIRA search failed: {e}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for MCP server"""
        confluence_test = await self.test_confluence_connection()
        jira_test = await self.test_jira_connection()
        
        return {
            "status": "healthy" if self._initialized else "not_initialized",
            "confluence": confluence_test,
            "jira": jira_test,
            "atlassian_library": ATLASSIAN_AVAILABLE
        }
    
    async def run_server(self):
        """Run the MCP server (simple test mode)"""
        logger.info("🚀 Starting MCP Atlassian Server")
        
        # Initialize
        if not await self.initialize():
            logger.error("❌ Failed to initialize server")
            return False
        
        # Run health check
        health = await self.health_check()
        logger.info(f"Health check results: {json.dumps(health, indent=2)}")
        
        # Test search if we have connections
        if self.confluence_client:
            logger.info("🔍 Testing Confluence search...")
            results = await self.search_confluence("test", max_results=3)
            logger.info(f"Found {len(results)} Confluence results")
            
        if self.jira_client:
            logger.info("🔍 Testing JIRA search...")
            results = await self.search_jira("bug", max_results=3)
            logger.info(f"Found {len(results)} JIRA results")
        
        logger.info("✅ MCP server test completed")
        return True


def load_config_from_file(config_path: str) -> AtlassianConfig:
    """Load configuration from JSON file"""
    try:
        with open(config_path, 'r') as f:
            data = json.load(f)
        
        confluence_config = data.get('confluence', {})
        jira_config = data.get('jira', {})
        
        return AtlassianConfig(
            confluence_url=confluence_config.get('server_url'),
            confluence_username=confluence_config.get('username'),
            confluence_api_token=confluence_config.get('api_token'),
            jira_url=jira_config.get('server_url'),
            jira_username=jira_config.get('username'), 
            jira_api_token=jira_config.get('api_token')
        )
        
    except Exception as e:
        logger.error(f"Failed to load config from {config_path}: {e}")
        return AtlassianConfig()


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='MCP Atlassian Server')
    parser.add_argument('--config', default='config.json', help='Config file path')
    parser.add_argument('--test', action='store_true', help='Run in test mode')
    parser.add_argument('--help-install', action='store_true', help='Show installation help')
    
    args = parser.parse_args()
    
    if args.help_install:
        print("🔧 Installation Requirements:")
        print("pip install atlassian-python-api")
        print("")
        print("📝 Configuration:")
        print("Create config.json with your Confluence/JIRA credentials")
        return
    
    # Load configuration
    config = load_config_from_file(args.config)
    
    # Create and run server
    server = MCPAtlassianServer(config)
    
    if args.test:
        success = await server.run_server()
        sys.exit(0 if success else 1)
    else:
        print("🚀 MCP Atlassian Server")
        print("Use --test to run connectivity tests")
        print("Use --help-install for setup instructions")


if __name__ == "__main__":
    asyncio.run(main())