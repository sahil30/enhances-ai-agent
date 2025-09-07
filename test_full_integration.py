#!/usr/bin/env python3
"""
Full Integration Test Suite

This script performs comprehensive testing of the AI agent with all integrations:
- Basic AI agent functionality
- Atlassian MCP integration
- Docker integration
- Configuration validation
"""

import asyncio
import os
import sys
import subprocess
import time
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def run_command(cmd, timeout=30):
    """Run a shell command and return result"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "Command timed out"


def print_section(title):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_test(name, status, message=""):
    """Print test result"""
    status_symbol = "✅" if status else "❌"
    print(f"{status_symbol} {name}")
    if message:
        print(f"   {message}")


async def test_basic_imports():
    """Test basic Python imports"""
    print_section("Basic Import Tests")
    
    tests = [
        ("Core AI agent", "from ai_agent.core.config import load_config"),
        ("MCP base classes", "from ai_agent.mcp import MCPClient, MCPConnectionError"),
        ("Atlassian integration", "from ai_agent.mcp import AtlassianMCPClient, AtlassianConfig"),
        ("Configuration module", "import atlassian_config"),
        ("API components", "from ai_agent.api import router"),
        ("Infrastructure", "from ai_agent.infrastructure.monitoring import HealthMonitor")
    ]
    
    results = []
    for name, import_statement in tests:
        try:
            exec(import_statement)
            print_test(name, True)
            results.append(True)
        except Exception as e:
            print_test(name, False, str(e))
            results.append(False)
    
    return all(results)


async def test_configuration():
    """Test configuration loading"""
    print_section("Configuration Tests")
    
    # Check if .env exists
    env_exists = os.path.exists(".env")
    print_test(".env file exists", env_exists)
    
    if not env_exists:
        print("   Creating test .env file...")
        # Create minimal test config
        with open(".env", "w") as f:
            f.write("LOG_LEVEL=INFO\nENABLE_METRICS=true\n")
    
    # Test configuration loading
    try:
        from ai_agent.core.config import load_config
        config = load_config()
        print_test("Configuration loading", True)
        return True
    except Exception as e:
        print_test("Configuration loading", False, str(e))
        return False


async def test_docker():
    """Test Docker availability and images"""
    print_section("Docker Integration Tests")
    
    # Check Docker
    returncode, stdout, stderr = run_command("docker --version")
    docker_available = returncode == 0
    print_test("Docker installed", docker_available, stdout.strip() if docker_available else stderr)
    
    if not docker_available:
        return False
    
    # Check if Docker is running
    returncode, stdout, stderr = run_command("docker info")
    docker_running = returncode == 0
    print_test("Docker running", docker_running)
    
    if not docker_running:
        return False
    
    # Check for mcp-atlassian image
    returncode, stdout, stderr = run_command("docker images ghcr.io/sooperset/mcp-atlassian:latest")
    image_available = "mcp-atlassian" in stdout
    print_test("mcp-atlassian image available", image_available)
    
    if not image_available:
        print("   Pulling mcp-atlassian image...")
        returncode, stdout, stderr = run_command("docker pull ghcr.io/sooperset/mcp-atlassian:latest", timeout=120)
        image_pulled = returncode == 0
        print_test("mcp-atlassian image pull", image_pulled)
        return image_pulled
    
    return True


async def test_atlassian_config():
    """Test Atlassian configuration options"""
    print_section("Atlassian Configuration Tests")
    
    try:
        from atlassian_config import (
            AtlassianCloudConfig, 
            AtlassianServerConfig, 
            AtlassianOAuthConfig,
            get_recommended_tools
        )
        
        # Test configuration classes
        print_test("Configuration classes import", True)
        
        # Test recommended tools
        tools = get_recommended_tools()
        tools_valid = isinstance(tools, dict) and "read_only" in tools
        print_test("Recommended tools", tools_valid)
        
        # Test cloud config creation (with dummy data)
        try:
            cloud_config = AtlassianCloudConfig(
                confluence_url="https://test.atlassian.net/wiki",
                confluence_username="test@test.com",
                confluence_api_token="test-token",
                jira_url="https://test.atlassian.net",
                jira_username="test@test.com",
                jira_api_token="test-token"
            )
            atlassian_config = cloud_config.to_atlassian_config()
            print_test("Cloud configuration creation", True)
        except Exception as e:
            print_test("Cloud configuration creation", False, str(e))
            return False
        
        return True
        
    except Exception as e:
        print_test("Atlassian configuration", False, str(e))
        return False


async def test_mcp_integration():
    """Test MCP integration (without actual connections)"""
    print_section("MCP Integration Tests")
    
    try:
        from ai_agent.mcp import AtlassianMCPClient, AtlassianConfig
        
        # Create test configuration
        config = AtlassianConfig(
            confluence_url="https://test.atlassian.net/wiki",
            confluence_username="test@test.com",
            confluence_api_token="test-token",
            jira_url="https://test.atlassian.net",
            jira_username="test@test.com",
            jira_api_token="test-token"
        )
        
        # Test client creation
        client = AtlassianMCPClient(config)
        print_test("Atlassian MCP client creation", True)
        
        # Test docker args building
        args = client._build_docker_args()
        args_valid = isinstance(args, list) and "docker" in args
        print_test("Docker args building", args_valid)
        
        # Test environment building
        env = client._build_environment()
        env_valid = isinstance(env, dict) and "CONFLUENCE_URL" in env
        print_test("Environment building", env_valid)
        
        return True
        
    except Exception as e:
        print_test("MCP integration", False, str(e))
        return False


async def test_scripts():
    """Test run scripts"""
    print_section("Script Tests")
    
    # Test run.sh
    run_sh_exists = os.path.exists("run.sh") and os.access("run.sh", os.X_OK)
    print_test("run.sh executable", run_sh_exists)
    
    # Test build.sh
    build_sh_exists = os.path.exists("build.sh") and os.access("build.sh", os.X_OK)
    print_test("build.sh executable", build_sh_exists)
    
    # Test run_docker.sh
    run_docker_sh_exists = os.path.exists("run_docker.sh") and os.access("run_docker.sh", os.X_OK)
    print_test("run_docker.sh executable", run_docker_sh_exists)
    
    # Test run.sh help
    if run_sh_exists:
        returncode, stdout, stderr = run_command("./run.sh help")
        help_works = returncode == 0 and "Usage:" in stdout
        print_test("run.sh help command", help_works)
    
    return all([run_sh_exists, build_sh_exists, run_docker_sh_exists])


async def test_health_check():
    """Test health check functionality"""
    print_section("Health Check Tests")
    
    try:
        # Test health check import
        from ai_agent.core.context_managers import ManagedAIAgent
        print_test("Health check import", True)
        
        # Create agent and test health check
        agent = ManagedAIAgent()
        health = await agent.health_check()
        
        health_valid = isinstance(health, dict) and "status" in health
        print_test("Health check execution", health_valid)
        
        # Clean up
        try:
            await agent.close()
        except:
            pass
        
        return health_valid
        
    except Exception as e:
        print_test("Health check", False, str(e))
        return False


async def test_api_components():
    """Test API components"""
    print_section("API Component Tests")
    
    try:
        # Test FastAPI import and setup
        from fastapi import FastAPI
        from ai_agent.api.router import router
        
        app = FastAPI()
        app.include_router(router)
        print_test("API setup", True)
        
        # Test if main endpoints exist
        routes = [route.path for route in app.routes]
        health_endpoint = "/health" in routes
        print_test("Health endpoint exists", health_endpoint)
        
        return True
        
    except Exception as e:
        print_test("API components", False, str(e))
        return False


async def run_integration_test():
    """Run a simple integration test if possible"""
    print_section("Integration Test")
    
    # Only run if we have proper configuration
    try:
        from atlassian_config import create_cloud_config_from_env, create_server_config_from_env
        from ai_agent.mcp import AtlassianMCPClient
        
        # Try to create configuration from environment
        config = None
        config_type = "none"
        
        try:
            cloud_config = create_cloud_config_from_env()
            config = cloud_config.to_atlassian_config()
            config_type = "cloud"
        except ValueError:
            try:
                server_config = create_server_config_from_env()
                config = server_config.to_atlassian_config()
                config_type = "server"
            except ValueError:
                pass
        
        if config is None:
            print_test("Integration test", False, "No valid configuration found")
            print("   Set up Atlassian credentials in .env to run integration test")
            return False
        
        print_test(f"Configuration type: {config_type}", True)
        
        # Test client creation
        client = AtlassianMCPClient(config)
        
        # Simple health check (doesn't start server)
        health = await client.health_check()
        print_test("Client health check", True, f"Status: {health.get('status', 'unknown')}")
        
        return True
        
    except Exception as e:
        print_test("Integration test", False, str(e))
        return False


async def main():
    """Run all tests"""
    print_section("AI Agent Full Integration Test Suite")
    
    test_results = []
    
    # Run all test suites
    test_results.append(await test_basic_imports())
    test_results.append(await test_configuration())
    test_results.append(await test_docker())
    test_results.append(await test_atlassian_config())
    test_results.append(await test_mcp_integration())
    test_results.append(await test_scripts())
    test_results.append(await test_health_check())
    test_results.append(await test_api_components())
    test_results.append(await run_integration_test())
    
    # Summary
    print_section("Test Summary")
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! The AI Agent integration is working correctly.")
        print("\nNext steps:")
        print("1. Configure your .env file with real Atlassian credentials")
        print("2. Run: ./run.sh test-atlassian")
        print("3. Start the agent: ./run.sh interactive")
        print("4. Or use Docker: ./run_docker.sh build && ./run_docker.sh start")
    else:
        failed = total - passed
        print(f"\n⚠️  {failed} test(s) failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("1. Make sure all dependencies are installed: ./build.sh")
        print("2. Check Docker installation and status")
        print("3. Verify your .env file configuration")
        
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)