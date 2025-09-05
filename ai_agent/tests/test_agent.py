import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ai_agent.core.agent import AIAgent
from ai_agent.core.config import Config
from ai_agent.core.ai_client import CustomAIClient
from ai_agent.mcp import ConfluenceMCPClient, JiraMCPClient
from ai_agent.core.code_reader import CodeRepositoryReader


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    config = Mock(spec=Config)
    config.custom_ai_api_url = "https://api.test.com/v1/chat"
    config.custom_ai_api_key = "test-key"
    config.confluence_access_token = "confluence-token"
    config.confluence_base_url = "https://test.atlassian.net/wiki"
    config.confluence_mcp_server_url = "ws://localhost:3001"
    config.jira_access_token = "jira-token"
    config.jira_base_url = "https://test.atlassian.net"
    config.jira_mcp_server_url = "ws://localhost:3002"
    config.code_repo_path = "./test-repo"
    return config


@pytest.fixture
def mock_confluence_data():
    """Mock Confluence search results"""
    return [
        {
            "id": "123456",
            "title": "API Authentication Guide",
            "excerpt": "How to authenticate with our API",
            "url": "https://test.atlassian.net/wiki/spaces/DOC/pages/123456",
            "space": "Documentation",
            "content": "This guide explains how to authenticate with our REST API using tokens..."
        },
        {
            "id": "789012",
            "title": "Error Handling Best Practices",
            "excerpt": "Best practices for handling errors in applications",
            "url": "https://test.atlassian.net/wiki/spaces/DEV/pages/789012",
            "space": "Development",
            "content": "When building robust applications, proper error handling is crucial..."
        }
    ]


@pytest.fixture
def mock_jira_data():
    """Mock JIRA search results"""
    return [
        {
            "key": "PROJ-123",
            "id": "10001",
            "summary": "API authentication failing with 401 error",
            "description": "Users are getting 401 errors when trying to authenticate",
            "status": "In Progress",
            "priority": "High",
            "assignee": "John Doe",
            "url": "https://test.atlassian.net/browse/PROJ-123"
        },
        {
            "key": "PROJ-124",
            "id": "10002",
            "summary": "Implement better error messages for API",
            "description": "API should return more descriptive error messages",
            "status": "Open",
            "priority": "Medium",
            "assignee": "Jane Smith",
            "url": "https://test.atlassian.net/browse/PROJ-124"
        }
    ]


@pytest.fixture
def mock_code_data():
    """Mock code search results"""
    return [
        {
            "file_path": "src/auth/AuthService.java",
            "file_type": "java",
            "content_preview": "public class AuthService { public boolean authenticate(String token) { ... } }",
            "matches": [
                {"line_number": 15, "line_content": "public boolean authenticate(String token) {"}
            ],
            "analysis": {"classes": ["AuthService"], "methods": ["authenticate"]}
        },
        {
            "file_path": "src/utils/ErrorHandler.py",
            "file_type": "python",
            "content_preview": "def handle_auth_error(error): return {'status': 401, 'message': 'Authentication failed'}",
            "matches": [
                {"line_number": 23, "line_content": "def handle_auth_error(error):"}
            ],
            "analysis": {"functions": ["handle_auth_error"]}
        }
    ]


@pytest.fixture
async def ai_agent(mock_config):
    """Create AI agent instance for testing"""
    with patch('agent.CustomAIClient') as mock_ai_client, \
         patch('agent.ConfluenceMCPClient') as mock_confluence_client, \
         patch('agent.JiraMCPClient') as mock_jira_client, \
         patch('agent.CodeRepositoryReader') as mock_code_reader:
        
        # Setup mocks
        mock_ai_client.return_value = AsyncMock()
        mock_confluence_client.return_value = AsyncMock()
        mock_jira_client.return_value = AsyncMock()
        mock_code_reader.return_value = Mock()
        
        agent = AIAgent(mock_config)
        yield agent
        
        # Cleanup
        await agent.close()


class TestAIAgent:
    """Test cases for AIAgent class"""
    
    @pytest.mark.asyncio
    async def test_process_query_success(self, ai_agent, mock_confluence_data, mock_jira_data, mock_code_data):
        """Test successful query processing"""
        # Mock search results
        ai_agent.confluence_client.search_pages = AsyncMock(return_value=mock_confluence_data)
        ai_agent.jira_client.search_by_text = AsyncMock(return_value=mock_jira_data)
        ai_agent.code_reader.search_files = Mock(return_value=mock_code_data)
        ai_agent.ai_client.analyze_context = AsyncMock(return_value="Based on the search results, here's how to fix authentication issues...")
        
        query = "how to fix API authentication errors"
        result = await ai_agent.process_query(query)
        
        assert result["query"] == query
        assert "solution" in result
        assert result["sources"]["confluence"]["count"] == 2
        assert result["sources"]["jira"]["count"] == 2
        assert result["sources"]["code"]["count"] == 2
        
        # Verify search methods were called
        ai_agent.confluence_client.search_pages.assert_called_once_with(query, 10)
        ai_agent.jira_client.search_by_text.assert_called_once_with(query, 10)
        ai_agent.code_reader.search_files.assert_called_once_with(query, None)
    
    @pytest.mark.asyncio
    async def test_process_query_with_options(self, ai_agent, mock_confluence_data):
        """Test query processing with search options"""
        ai_agent.confluence_client.search_pages = AsyncMock(return_value=mock_confluence_data)
        ai_agent.jira_client.search_by_text = AsyncMock(return_value=[])
        ai_agent.code_reader.search_files = Mock(return_value=[])
        ai_agent.ai_client.analyze_context = AsyncMock(return_value="Solution based on Confluence docs only")
        
        search_options = {
            "search_jira": False,
            "search_code": False,
            "max_results": 5
        }
        
        query = "API documentation"
        result = await ai_agent.process_query(query, search_options)
        
        assert result["sources"]["confluence"]["count"] == 2
        assert result["sources"]["jira"]["count"] == 0
        assert result["sources"]["code"]["count"] == 0
        
        ai_agent.confluence_client.search_pages.assert_called_once_with(query, 5)
    
    @pytest.mark.asyncio
    async def test_process_query_error_handling(self, ai_agent):
        """Test error handling in query processing"""
        # Mock an exception in Confluence search
        ai_agent.confluence_client.search_pages = AsyncMock(side_effect=Exception("Connection failed"))
        ai_agent.jira_client.search_by_text = AsyncMock(return_value=[])
        ai_agent.code_reader.search_files = Mock(return_value=[])
        ai_agent.ai_client.analyze_context = AsyncMock(return_value="Limited results due to connection issues")
        
        query = "test query"
        result = await ai_agent.process_query(query)
        
        # Should still return a result, even with one source failing
        assert "solution" in result
        assert result["sources"]["confluence"]["count"] == 0
    
    @pytest.mark.asyncio
    async def test_get_detailed_info_confluence(self, ai_agent):
        """Test getting detailed Confluence page info"""
        expected_content = {
            "id": "123456",
            "title": "Detailed API Guide",
            "content": "Full content of the API guide...",
            "space": {"name": "Documentation"}
        }
        
        ai_agent.confluence_client.get_page_content = AsyncMock(return_value=expected_content)
        
        result = await ai_agent.get_detailed_info("confluence", "123456")
        
        assert result == expected_content
        ai_agent.confluence_client.get_page_content.assert_called_once_with("123456")
    
    @pytest.mark.asyncio
    async def test_get_detailed_info_jira(self, ai_agent):
        """Test getting detailed JIRA issue info"""
        expected_details = {
            "key": "PROJ-123",
            "fields": {
                "summary": "API issue",
                "description": "Detailed description",
                "status": {"name": "In Progress"}
            }
        }
        
        ai_agent.jira_client.get_issue_details = AsyncMock(return_value=expected_details)
        
        result = await ai_agent.get_detailed_info("jira", "PROJ-123")
        
        assert result == expected_details
        ai_agent.jira_client.get_issue_details.assert_called_once_with("PROJ-123")
    
    @pytest.mark.asyncio
    async def test_get_detailed_info_code(self, ai_agent):
        """Test getting detailed code file info"""
        expected_file_info = {
            "file_path": "src/test.py",
            "file_type": "python",
            "content": "def test_function():\n    pass",
            "analysis": {"functions": ["test_function"]}
        }
        
        ai_agent.code_reader.get_file_content = Mock(return_value=expected_file_info)
        
        result = await ai_agent.get_detailed_info("code", "src/test.py")
        
        assert result == expected_file_info
        ai_agent.code_reader.get_file_content.assert_called_once_with("src/test.py")
    
    @pytest.mark.asyncio
    async def test_get_detailed_info_invalid_type(self, ai_agent):
        """Test getting detailed info with invalid type"""
        result = await ai_agent.get_detailed_info("invalid", "test-id")
        
        assert "error" in result
        assert "Unknown item type" in result["error"]
    
    @pytest.mark.asyncio
    async def test_suggest_related_queries(self, ai_agent):
        """Test related query suggestions"""
        context = {
            "sources": {
                "confluence": {"data": [{"title": "Authentication Guide"}]},
                "jira": {"data": [{"summary": "Login issues"}]},
                "code": {"data": [{"file_path": "auth.py"}]}
            }
        }
        
        ai_agent.ai_client.generate_response = AsyncMock(
            return_value="- How to implement OAuth authentication\n- Troubleshooting login errors\n- API token management"
        )
        
        suggestions = await ai_agent.suggest_related_queries("authentication", context)
        
        assert len(suggestions) == 3
        assert "OAuth authentication" in suggestions[0]
        assert "login errors" in suggestions[1]
        assert "token management" in suggestions[2]


@pytest.mark.asyncio
async def test_agent_initialization(mock_config):
    """Test agent initialization"""
    with patch('agent.CustomAIClient') as mock_ai_client, \
         patch('agent.ConfluenceMCPClient') as mock_confluence_client, \
         patch('agent.JiraMCPClient') as mock_jira_client, \
         patch('agent.CodeRepositoryReader') as mock_code_reader:
        
        agent = AIAgent(mock_config)
        
        # Verify clients were initialized with correct config
        mock_ai_client.assert_called_once_with(mock_config)
        mock_confluence_client.assert_called_once_with(mock_config)
        mock_jira_client.assert_called_once_with(mock_config)
        mock_code_reader.assert_called_once_with(mock_config.code_repo_path)
        
        await agent.close()


@pytest.mark.asyncio
async def test_agent_close(ai_agent):
    """Test agent cleanup"""
    # Mock the close methods
    ai_agent.ai_client.close = AsyncMock()
    ai_agent.confluence_client.disconnect = AsyncMock()
    ai_agent.jira_client.disconnect = AsyncMock()
    
    await ai_agent.close()
    
    # Verify all clients were closed
    ai_agent.ai_client.close.assert_called_once()
    ai_agent.confluence_client.disconnect.assert_called_once()
    ai_agent.jira_client.disconnect.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])