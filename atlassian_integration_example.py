"""
Example usage of the Atlassian MCP Client integration

This example demonstrates how to use the integrated mcp-atlassian server
with your AI agent for both Confluence and Jira operations.
"""

import asyncio
import os
from ai_agent.mcp import AtlassianMCPClient, AtlassianConfig


async def example_confluence_operations():
    """Example Confluence operations using the integrated MCP client"""
    
    # Configure Atlassian connection (Cloud example)
    config = AtlassianConfig(
        confluence_url="https://your-company.atlassian.net/wiki",
        confluence_username="your.email@company.com",
        confluence_api_token=os.getenv("CONFLUENCE_API_TOKEN"),
        
        jira_url="https://your-company.atlassian.net",
        jira_username="your.email@company.com", 
        jira_api_token=os.getenv("JIRA_API_TOKEN"),
        
        # Optional: Filter specific spaces/projects
        confluence_spaces_filter="DEV,TEAM,DOC",
        jira_projects_filter="PROJ,DEV,SUPPORT",
        
        # Optional: Enable verbose logging
        mcp_verbose=True,
        mcp_logging_stdout=True
    )
    
    # Use the client with async context manager
    async with AtlassianMCPClient(config) as client:
        
        # Confluence operations
        print("=== Confluence Operations ===")
        
        # Search for pages
        pages = await client.confluence_search(
            query="space = DEV AND title ~ 'API*'",
            limit=10
        )
        print(f"Found {len(pages)} pages matching search")
        
        # Get page details
        if pages:
            page = await client.confluence_get_page(
                page_id=pages[0]["id"],
                expand=["body.storage", "version"]
            )
            print(f"Page title: {page.get('title')}")
            print(f"Page version: {page.get('version', {}).get('number')}")
        
        # Create a new page
        new_page = await client.confluence_create_page(
            space_key="DEV",
            title="AI Agent Integration Test",
            content="<p>This page was created by the AI agent using the mcp-atlassian integration.</p>"
        )
        print(f"Created page: {new_page.get('title')} (ID: {new_page.get('id')})")
        
        # Jira operations
        print("\n=== Jira Operations ===")
        
        # Search for issues
        issues = await client.jira_search(
            jql="project = PROJ AND status = 'To Do'",
            fields=["summary", "status", "assignee"],
            max_results=5
        )
        print(f"Found {len(issues)} issues in To Do status")
        
        # Get issue details
        if issues:
            issue = await client.jira_get_issue(
                issue_key=issues[0]["key"],
                expand=["changelog", "comments"]
            )
            print(f"Issue: {issue.get('key')} - {issue.get('fields', {}).get('summary')}")
        
        # Create a new issue
        new_issue = await client.jira_create_issue(
            project_key="PROJ",
            summary="AI Agent Integration Test",
            description="This issue was created by the AI agent using the mcp-atlassian integration.",
            issue_type="Task"
        )
        print(f"Created issue: {new_issue.get('key')}")
        
        # Add comment to the new issue
        await client.jira_add_comment(
            issue_key=new_issue.get('key'),
            comment="This is an automated comment from the AI agent."
        )
        print(f"Added comment to issue: {new_issue.get('key')}")
        
        # Health check
        print("\n=== Health Check ===")
        health = await client.health_check()
        print(f"Server status: {health.get('status')}")
        print(f"Available tools: {len(health.get('tools', []))}")


async def example_server_datacenter_operations():
    """Example for Server/Data Center deployment"""
    
    config = AtlassianConfig(
        confluence_url="https://confluence.your-company.com",
        confluence_personal_token=os.getenv("CONFLUENCE_PAT"),
        confluence_ssl_verify=False,  # If using self-signed certificates
        
        jira_url="https://jira.your-company.com", 
        jira_personal_token=os.getenv("JIRA_PAT"),
        jira_ssl_verify=False,
        
        # Enable read-only mode if needed
        read_only_mode=True
    )
    
    async with AtlassianMCPClient(config) as client:
        # Get all available projects
        projects = await client.jira_get_all_projects()
        print(f"Available projects: {[p.get('key') for p in projects]}")
        
        # Search confluence with space restriction
        pages = await client.confluence_search("type = page", limit=5)
        print(f"Found {len(pages)} pages")


async def example_oauth_operations():
    """Example using OAuth 2.0 authentication (Cloud only)"""
    
    config = AtlassianConfig(
        confluence_url="https://your-company.atlassian.net/wiki",
        jira_url="https://your-company.atlassian.net",
        
        # OAuth configuration
        oauth_cloud_id=os.getenv("ATLASSIAN_OAUTH_CLOUD_ID"),
        oauth_client_id=os.getenv("ATLASSIAN_OAUTH_CLIENT_ID"),
        oauth_client_secret=os.getenv("ATLASSIAN_OAUTH_CLIENT_SECRET"),
        oauth_redirect_uri="http://localhost:8080/callback",
        oauth_scope="read:jira-work write:jira-work read:confluence-content.all write:confluence-content offline_access"
    )
    
    async with AtlassianMCPClient(config) as client:
        # Perform operations using OAuth authentication
        tools = await client.get_available_tools()
        print(f"Available tools with OAuth: {tools}")


async def main():
    """Run examples"""
    print("Atlassian MCP Integration Examples")
    print("=" * 50)
    
    try:
        # Choose which example to run based on your setup
        await example_confluence_operations()
        
        # Uncomment for Server/Data Center
        # await example_server_datacenter_operations()
        
        # Uncomment for OAuth
        # await example_oauth_operations()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Make sure to:")
        print("1. Set the required environment variables (API tokens, URLs)")
        print("2. Have Docker installed and running")
        print("3. Ensure mcp-atlassian Docker image is available")


if __name__ == "__main__":
    # Set up environment variables before running
    # export CONFLUENCE_API_TOKEN="your_token"
    # export JIRA_API_TOKEN="your_token"
    
    asyncio.run(main())