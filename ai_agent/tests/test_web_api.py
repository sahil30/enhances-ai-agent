import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_agent():
    """Mock AI agent for testing"""
    agent = AsyncMock()
    agent.process_query = AsyncMock(return_value={
        "query": "test query",
        "solution": "Test solution",
        "sources": {
            "confluence": {"count": 2, "data": []},
            "jira": {"count": 1, "data": []},
            "code": {"count": 1, "data": []}
        }
    })
    agent.close = AsyncMock()
    return agent


@pytest.fixture
def mock_cache_manager():
    """Mock cache manager for testing"""
    cache = AsyncMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    cache.initialize = AsyncMock()
    cache.close = AsyncMock()
    cache.get_stats = AsyncMock(return_value={
        "memory_cache": {"size": 10, "maxsize": 100},
        "file_cache": {"file_count": 5, "total_size_mb": 1.2}
    })
    return cache


@pytest.fixture
def mock_batch_processor():
    """Mock batch processor for testing"""
    processor = AsyncMock()
    processor.start_workers = AsyncMock()
    processor.stop_workers = AsyncMock()
    processor.process_queries_batch = AsyncMock(return_value="batch-123")
    processor.get_batch_status = AsyncMock(return_value={
        "batch_id": "batch-123",
        "status": "completed",
        "total_tasks": 3,
        "completed_tasks": 3,
        "progress_percentage": 100
    })
    processor.get_batch_results = AsyncMock(return_value={
        "batch_id": "batch-123",
        "total_tasks": 3,
        "completed_tasks": 3,
        "failed_tasks": 0,
        "success_rate": 100,
        "results": []
    })
    processor.get_system_stats = Mock(return_value={
        "workers": {"total_workers": 10, "active_workers": 10},
        "queue": {"queue_size": 0, "total_tasks": 100}
    })
    return processor


@pytest.fixture
def client():
    """Create test client with mocked dependencies"""
    with patch('web_api.load_config') as mock_config, \
         patch('web_api.AIAgent') as mock_agent_class, \
         patch('web_api.CacheManager') as mock_cache_class, \
         patch('web_api.batch_processor') as mock_batch, \
         patch('web_api.performance_monitor') as mock_monitor, \
         patch('web_api.plugin_manager') as mock_plugins, \
         patch('web_api.semantic_search') as mock_semantic, \
         patch('web_api.query_processor') as mock_query_proc:
        
        # Mock configuration
        config = Mock()
        config.use_redis = False
        mock_config.return_value = config
        
        # Mock agent
        agent_instance = AsyncMock()
        agent_instance.process_query = AsyncMock(return_value={
            "query": "test",
            "solution": "test solution",
            "sources": {"confluence": {"count": 0, "data": []}}
        })
        mock_agent_class.return_value = agent_instance
        
        # Mock cache manager
        cache_instance = AsyncMock()
        cache_instance.initialize = AsyncMock()
        cache_instance.get = AsyncMock(return_value=None)
        cache_instance.set = AsyncMock()
        cache_instance.get_stats = AsyncMock(return_value={})
        mock_cache_class.return_value = cache_instance
        
        # Mock other components
        mock_batch.start_workers = AsyncMock()
        mock_batch.stop_workers = AsyncMock()
        mock_monitor.start_monitoring = AsyncMock()
        mock_monitor.stop_monitoring = AsyncMock()
        mock_plugins.load_plugins = AsyncMock()
        mock_plugins.cleanup_all_plugins = AsyncMock()
        
        # Import after mocking
        from web_api import app
        
        # Set global variables
        import web_api
        web_api.agent_instance = agent_instance
        web_api.cache_manager = cache_instance
        
        with TestClient(app) as test_client:
            yield test_client


class TestWebAPI:
    """Test cases for Web API endpoints"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "AI Agent API is running" in data["data"]["message"]
    
    def test_search_endpoint_success(self, client):
        """Test successful search request"""
        request_data = {
            "query": "how to implement authentication",
            "search_options": {"max_results": 5},
            "use_cache": True
        }
        
        response = client.post("/search", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["query"] == request_data["query"]
        assert "solution" in data["data"]
        assert "sources" in data["data"]
    
    def test_search_endpoint_validation_error(self, client):
        """Test search request with validation error"""
        # Empty query should fail validation
        request_data = {
            "query": "",
            "use_cache": False
        }
        
        response = client.post("/search", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_search_endpoint_missing_query(self, client):
        """Test search request without query field"""
        request_data = {
            "search_options": {"max_results": 5}
        }
        
        response = client.post("/search", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_batch_search_endpoint(self, client):
        """Test batch search submission"""
        with patch('web_api.batch_processor') as mock_batch:
            mock_batch.process_queries_batch = AsyncMock(return_value="batch-123")
            
            request_data = {
                "queries": [
                    "how to authenticate users",
                    "database connection issues",
                    "API rate limiting"
                ],
                "search_options": {"max_results": 10}
            }
            
            response = client.post("/batch/search", json=request_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert data["data"]["batch_id"] == "batch-123"
            assert data["data"]["total_queries"] == 3
    
    def test_batch_search_validation_error(self, client):
        """Test batch search with validation error"""
        # Empty queries list should fail
        request_data = {
            "queries": []
        }
        
        response = client.post("/batch/search", json=request_data)
        assert response.status_code == 422
    
    def test_batch_search_too_many_queries(self, client):
        """Test batch search with too many queries"""
        # More than 50 queries should fail validation
        request_data = {
            "queries": [f"query {i}" for i in range(51)]
        }
        
        response = client.post("/batch/search", json=request_data)
        assert response.status_code == 422
    
    def test_batch_status_endpoint(self, client):
        """Test batch status retrieval"""
        with patch('web_api.batch_processor') as mock_batch:
            mock_batch.get_batch_status = AsyncMock(return_value={
                "batch_id": "batch-123",
                "status": "running",
                "total_tasks": 5,
                "completed_tasks": 2,
                "progress_percentage": 40
            })
            
            response = client.get("/batch/batch-123/status")
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert data["data"]["batch_id"] == "batch-123"
            assert data["data"]["progress_percentage"] == 40
    
    def test_batch_status_not_found(self, client):
        """Test batch status for non-existent batch"""
        with patch('web_api.batch_processor') as mock_batch:
            mock_batch.get_batch_status = AsyncMock(return_value=None)
            
            response = client.get("/batch/nonexistent/status")
            assert response.status_code == 404
    
    def test_batch_results_endpoint(self, client):
        """Test batch results retrieval"""
        with patch('web_api.batch_processor') as mock_batch:
            mock_batch.get_batch_results = AsyncMock(return_value={
                "batch_id": "batch-123",
                "total_tasks": 3,
                "completed_tasks": 3,
                "failed_tasks": 0,
                "success_rate": 100.0,
                "results": [{"task_id": "1", "result": "success"}]
            })
            
            response = client.get("/batch/batch-123/results")
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert data["data"]["success_rate"] == 100.0
            assert len(data["data"]["results"]) == 1
    
    def test_semantic_search_endpoint(self, client):
        """Test semantic search endpoint"""
        with patch('web_api.semantic_search') as mock_semantic:
            mock_result = Mock()
            mock_result.content = "Test content"
            mock_result.source = "test-source"
            mock_result.source_type = "confluence"
            mock_result.title = "Test Title"
            mock_result.url = "https://test.com"
            mock_result.combined_score = 0.9
            mock_result.semantic_score = 0.8
            mock_result.keyword_score = 0.7
            mock_result.metadata = {"test": "data"}
            
            mock_semantic.search = AsyncMock(return_value=[mock_result])
            
            request_data = {
                "query": "authentication methods",
                "source_types": ["confluence"],
                "limit": 10,
                "min_score": 0.5
            }
            
            response = client.post("/semantic/search", json=request_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["results"]) == 1
            assert data["data"]["results"][0]["title"] == "Test Title"
    
    def test_semantic_build_index_endpoint(self, client):
        """Test semantic index building"""
        with patch('web_api.semantic_search') as mock_semantic:
            mock_semantic.build_index = AsyncMock()
            
            request_data = {
                "source_type": "confluence",
                "documents": [
                    {"id": "1", "title": "Test Doc", "content": "Test content"}
                ],
                "rebuild": False
            }
            
            response = client.post("/semantic/build-index", json=request_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert data["data"]["source_type"] == "confluence"
            assert data["data"]["document_count"] == 1
    
    def test_semantic_stats_endpoint(self, client):
        """Test semantic search statistics"""
        with patch('web_api.semantic_search') as mock_semantic:
            mock_semantic.get_index_stats = Mock(return_value={
                "confluence": {"document_count": 100, "vocabulary_size": 5000},
                "jira": {"document_count": 50, "vocabulary_size": 2000}
            })
            
            response = client.get("/semantic/stats")
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert "confluence" in data["data"]
            assert "jira" in data["data"]
    
    def test_plugins_endpoint(self, client):
        """Test plugins listing"""
        with patch('web_api.plugin_manager') as mock_plugins:
            mock_plugins.get_plugin_status = Mock(return_value={
                "test_plugin": {
                    "name": "test_plugin",
                    "version": "1.0.0",
                    "enabled": True,
                    "type": "data_source"
                }
            })
            
            response = client.get("/plugins")
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert "test_plugin" in data["data"]
    
    def test_plugin_action_enable(self, client):
        """Test plugin enable action"""
        with patch('web_api.plugin_manager') as mock_plugins:
            mock_plugins.enable_plugin = AsyncMock(return_value=True)
            
            request_data = {
                "plugin_name": "test_plugin",
                "action": "enable"
            }
            
            response = client.post("/plugins/action", json=request_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
    
    def test_plugin_action_invalid(self, client):
        """Test invalid plugin action"""
        request_data = {
            "plugin_name": "test_plugin",
            "action": "invalid_action"
        }
        
        response = client.post("/plugins/action", json=request_data)
        assert response.status_code == 400
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "status" in data["data"]
        assert "services" in data["data"]
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint"""
        with patch('web_api.metrics_collector') as mock_metrics:
            mock_metrics.update_system_metrics = Mock()
            mock_metrics.get_metrics = Mock(return_value="# HELP test_metric\ntest_metric 1.0")
            
            response = client.get("/metrics")
            assert response.status_code == 200
            
            # Should return Prometheus format
            assert "test_metric" in response.text
    
    def test_stats_endpoint(self, client):
        """Test system statistics endpoint"""
        with patch('web_api.batch_processor') as mock_batch, \
             patch('web_api.semantic_search') as mock_semantic:
            
            mock_batch.get_system_stats = Mock(return_value={
                "workers": {"total_workers": 10}
            })
            mock_semantic.get_index_stats = Mock(return_value={
                "confluence": {"document_count": 100}
            })
            
            response = client.get("/stats")
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert "batch_processor" in data["data"]
            assert "semantic_search" in data["data"]
    
    def test_request_logging_middleware(self, client):
        """Test request logging middleware"""
        # Make a request to trigger middleware
        response = client.get("/")
        assert response.status_code == 200
        
        # Check that response headers are present (middleware ran)
        assert response.headers.get("content-type") is not None


class TestAPIValidation:
    """Test API input validation"""
    
    def test_query_request_validation(self):
        """Test QueryRequest model validation"""
        from web_api import QueryRequest
        
        # Valid request
        valid_request = QueryRequest(query="test query")
        assert valid_request.query == "test query"
        assert valid_request.use_cache is True
        
        # Invalid request - empty query should fail
        with pytest.raises(ValueError):
            QueryRequest(query="")
    
    def test_batch_query_request_validation(self):
        """Test BatchQueryRequest model validation"""
        from web_api import BatchQueryRequest
        
        # Valid request
        valid_request = BatchQueryRequest(queries=["query1", "query2"])
        assert len(valid_request.queries) == 2
        
        # Invalid - empty queries list
        with pytest.raises(ValueError):
            BatchQueryRequest(queries=[])
        
        # Invalid - too many queries
        with pytest.raises(ValueError):
            BatchQueryRequest(queries=[f"query{i}" for i in range(51)])
    
    def test_semantic_search_request_validation(self):
        """Test SemanticSearchRequest model validation"""
        from web_api import SemanticSearchRequest
        
        # Valid request
        valid_request = SemanticSearchRequest(
            query="test query",
            limit=10,
            min_score=0.5
        )
        assert valid_request.query == "test query"
        assert valid_request.limit == 10
        assert valid_request.min_score == 0.5
        
        # Invalid - limit too high
        with pytest.raises(ValueError):
            SemanticSearchRequest(query="test", limit=101)
        
        # Invalid - min_score out of range
        with pytest.raises(ValueError):
            SemanticSearchRequest(query="test", min_score=1.5)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])