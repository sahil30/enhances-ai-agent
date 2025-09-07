#!/usr/bin/env python3
"""
Test script for Atlassian MCP integration

This script tests the basic functionality of the Atlassian MCP client
integration with the AI agent.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the current directory to Python path so we can import ai_agent
sys.path.insert(0, str(Path(__file__).parent))

from ai_agent.mcp import AtlassianMCPClient, AtlassianConfig
from atlassian_config import create_cloud_config_from_env, create_server_config_from_env


async def test_connection():
    """Test basic connection to mcp-atlassian server"""
    
    print("Testing Atlassian MCP Integration")
    print("=" * 50)
    
    try:
        # Try to create configuration from environment
        try:
            cloud_config = create_cloud_config_from_env()
            config = cloud_config.to_atlassian_config()
            deployment_type = "Cloud (API Tokens)"
        except ValueError:
            try:
                server_config = create_server_config_from_env()
                config = server_config.to_atlassian_config()
                deployment_type = "Server/Data Center (PATs)"
            except ValueError:
                print("ERROR: No valid configuration found in environment variables.")
                print("Please set the required environment variables for either:")
                print("1. Cloud deployment (API tokens)")
                print("2. Server/Data Center deployment (Personal Access Tokens)")
                print("\nRun 'python atlassian_config.py' for setup instructions.")
                return False
        
        print(f"Configuration type: {deployment_type}")
        print(f"Confluence URL: {config.confluence_url}")
        print(f"Jira URL: {config.jira_url}")
        print()
        
        # Test client creation and connection
        print("Creating Atlassian MCP client...")
        client = AtlassianMCPClient(config)
        
        print("Starting mcp-atlassian server...")
        await client.start_server()
        
        if client.running:
            print("✓ Server started successfully")
        else:
            print("✗ Server failed to start")
            return False
        
        # Test health check
        print("Performing health check...")
        health = await client.health_check()
        
        if health.get("status") == "healthy":
            print("✓ Health check passed")
            tools = health.get("tools", [])
            print(f"✓ Available tools: {len(tools)}")
            if config.mcp_verbose:
                print(f"  Tools: {', '.join(tools[:10])}{'...' if len(tools) > 10 else ''}")
        else:
            print(f"✗ Health check failed: {health.get('error')}")
            return False
        
        # Test basic operations
        print("\nTesting basic operations...")
        
        # Test Jira - get projects
        try:
            projects = await client.jira_get_all_projects()
            print(f"✓ Jira: Found {len(projects)} projects")
            if projects and config.mcp_verbose:
                project_keys = [p.get("key") for p in projects[:5]]
                print(f"  Projects: {', '.join(project_keys)}{'...' if len(projects) > 5 else ''}")
        except Exception as e:
            print(f"✗ Jira test failed: {str(e)}")
        
        # Test Confluence - search pages  
        try:
            pages = await client.confluence_search("type = page", limit=5)
            print(f"✓ Confluence: Found {len(pages)} pages")
            if pages and config.mcp_verbose:
                page_titles = [p.get("title", "Untitled")[:30] for p in pages[:3]]
                print(f"  Pages: {', '.join(page_titles)}{'...' if len(pages) > 3 else ''}")
        except Exception as e:
            print(f"✗ Confluence test failed: {str(e)}")
        
        # Clean up
        print("\nCleaning up...")
        await client.stop_server()
        print("✓ Server stopped")
        
        print("\n" + "=" * 50)
        print("Integration test completed successfully!")
        print("The Atlassian MCP integration is working correctly.")
        return True
        
    except Exception as e:
        print(f"\nERROR: Integration test failed: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Ensure Docker is installed and running")
        print("2. Check that the mcp-atlassian image is available:")
        print("   docker pull ghcr.io/sooperset/mcp-atlassian:latest")
        print("3. Verify your Atlassian credentials and URLs")
        print("4. Check network connectivity to Atlassian servers")
        return False


async def test_specific_operations():
    """Test specific operations if basic test passes"""
    
    print("\nRunning specific operation tests...")
    
    try:
        # Use the same config setup as test_connection
        try:
            cloud_config = create_cloud_config_from_env()
            config = cloud_config.to_atlassian_config()
        except ValueError:
            server_config = create_server_config_from_env()
            config = server_config.to_atlassian_config()
        
        async with AtlassianMCPClient(config) as client:
            
            # Test Jira search
            print("Testing Jira search...")
            issues = await client.jira_search(
                jql="ORDER BY updated DESC",
                max_results=3
            )
            print(f"✓ Found {len(issues)} recent issues")
            
            # Test Confluence search with CQL
            print("Testing Confluence search...")
            pages = await client.confluence_search(
                query="type = page ORDER BY lastModified DESC", 
                limit=3
            )
            print(f"✓ Found {len(pages)} recent pages")
            
            print("✓ All specific operations completed successfully")
            
    except Exception as e:
        print(f"✗ Specific operations test failed: {str(e)}")


async def main():
    """Run all tests"""
    
    # Check for Docker
    try:
        proc = await asyncio.create_subprocess_exec(
            "docker", "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.communicate()
        if proc.returncode != 0:
            print("ERROR: Docker is not available or not working properly")
            print("Please install Docker and ensure it's running")
            return
    except FileNotFoundError:
        print("ERROR: Docker is not installed")
        print("Please install Docker from https://www.docker.com/")
        return
    
    # Run basic connection test
    if await test_connection():
        # Run specific operations test
        await test_specific_operations()
    
    print("\nTest completed. Check the output above for any issues.")


if __name__ == "__main__":
    asyncio.run(main())