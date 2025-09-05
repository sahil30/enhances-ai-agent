import pytest
import asyncio
import tempfile
import shutil
import time
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cache_manager import CacheManager, SmartCache


@pytest.fixture
def temp_cache_dir():
    """Create temporary directory for cache testing"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def cache_config(temp_cache_dir):
    """Cache configuration for testing"""
    return {
        'memory_cache_size': 100,
        'memory_cache_ttl': 5,  # 5 seconds for testing
        'file_cache_dir': temp_cache_dir,
        'use_redis': False,
        'confluence_cache_ttl': 10,
        'jira_cache_ttl': 8,
        'code_cache_ttl': 15,
        'ai_cache_ttl': 20
    }


@pytest.fixture
async def cache_manager(cache_config):
    """Create cache manager instance for testing"""
    manager = CacheManager(cache_config)
    await manager.initialize()
    yield manager
    await manager.close()


class TestCacheManager:
    """Test cases for CacheManager class"""
    
    @pytest.mark.asyncio
    async def test_memory_cache_basic_operations(self, cache_manager):
        """Test basic memory cache operations"""
        # Test set and get
        await cache_manager.set("test_key", {"data": "test_value"}, "test")
        result = await cache_manager.get("test_key", "test")
        
        assert result is not None
        assert result["data"] == "test_value"
    
    @pytest.mark.asyncio
    async def test_cache_miss(self, cache_manager):
        """Test cache miss scenario"""
        result = await cache_manager.get("nonexistent_key", "test")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_delete(self, cache_manager):
        """Test cache deletion"""
        # Set a value
        await cache_manager.set("delete_me", {"data": "value"}, "test")
        
        # Verify it exists
        result = await cache_manager.get("delete_me", "test")
        assert result is not None
        
        # Delete it
        await cache_manager.delete("delete_me", "test")
        
        # Verify it's gone
        result = await cache_manager.get("delete_me", "test")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_file_cache_persistence(self, cache_manager):
        """Test file cache persistence"""
        test_data = {"persistent": "data", "number": 42}
        
        # Set data
        await cache_manager.set("persistent_key", test_data, "test")
        
        # Clear memory cache to force file read
        cache_manager.memory_cache.clear()
        
        # Get data (should read from file)
        result = await cache_manager.get("persistent_key", "test")
        
        assert result is not None
        assert result["persistent"] == "data"
        assert result["number"] == 42
    
    @pytest.mark.asyncio
    async def test_cache_ttl_types(self, cache_manager):
        """Test different TTL values for different cache types"""
        # Set values with different cache types
        await cache_manager.set("confluence_key", {"type": "confluence"}, "confluence")
        await cache_manager.set("jira_key", {"type": "jira"}, "jira")
        await cache_manager.set("code_key", {"type": "code"}, "code")
        
        # All should be available immediately
        assert await cache_manager.get("confluence_key", "confluence") is not None
        assert await cache_manager.get("jira_key", "jira") is not None
        assert await cache_manager.get("code_key", "code") is not None
    
    @pytest.mark.asyncio
    async def test_cache_clear_by_type(self, cache_manager):
        """Test clearing cache by type"""
        # Set values of different types
        await cache_manager.set("key1", {"data": "value1"}, "type1")
        await cache_manager.set("key2", {"data": "value2"}, "type2")
        await cache_manager.set("key3", {"data": "value3"}, "type1")
        
        # Clear specific type
        await cache_manager.clear("type1")
        
        # type1 should be cleared, type2 should remain
        assert await cache_manager.get("key1", "type1") is None
        assert await cache_manager.get("key3", "type1") is None
        assert await cache_manager.get("key2", "type2") is not None
    
    @pytest.mark.asyncio
    async def test_cache_clear_all(self, cache_manager):
        """Test clearing all cache"""
        # Set multiple values
        await cache_manager.set("key1", {"data": "value1"}, "type1")
        await cache_manager.set("key2", {"data": "value2"}, "type2")
        
        # Clear all
        await cache_manager.clear()
        
        # All should be cleared from memory
        assert len(cache_manager.memory_cache) == 0
    
    @pytest.mark.asyncio
    async def test_cache_stats(self, cache_manager):
        """Test cache statistics"""
        # Add some data
        await cache_manager.set("stats_key1", {"data": "value1"}, "test")
        await cache_manager.set("stats_key2", {"data": "value2"}, "test")
        
        stats = await cache_manager.get_stats()
        
        assert "memory_cache" in stats
        assert stats["memory_cache"]["size"] >= 2
        assert "file_cache" in stats
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_files(self, cache_manager):
        """Test cleanup of expired file cache entries"""
        # Set data with short TTL
        await cache_manager.set("expire_test", {"data": "value"}, "test")
        
        # Manually expire the file by modifying its content
        cache_key = cache_manager._generate_key("expire_test", "test")
        file_path = cache_manager.file_cache_dir / f"{cache_key}.json"
        
        if file_path.exists():
            import json
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Set expiry time to past
            data['expires_at'] = time.time() - 1
            
            with open(file_path, 'w') as f:
                json.dump(data, f)
            
            # Run cleanup
            await cache_manager.cleanup_expired()
            
            # File should be removed
            assert not file_path.exists()
    
    @pytest.mark.asyncio
    async def test_key_generation(self, cache_manager):
        """Test cache key generation"""
        key1 = cache_manager._generate_key("test_key", "test_type")
        key2 = cache_manager._generate_key("test_key", "test_type")
        key3 = cache_manager._generate_key("different_key", "test_type")
        
        # Same input should generate same key
        assert key1 == key2
        
        # Different input should generate different key
        assert key1 != key3
        
        # Key should include type prefix
        assert "test_type" in key1


class TestSmartCache:
    """Test cases for SmartCache decorator"""
    
    @pytest.mark.asyncio
    async def test_smart_cache_decorator(self, cache_manager):
        """Test SmartCache decorator functionality"""
        call_count = 0
        
        @SmartCache(cache_manager, "test_cache")
        async def expensive_function(param1, param2=None):
            nonlocal call_count
            call_count += 1
            return f"result_{param1}_{param2}_{call_count}"
        
        # First call should execute function
        result1 = await expensive_function("a", param2="b")
        assert call_count == 1
        assert "result_a_b_1" == result1
        
        # Second call with same params should use cache
        result2 = await expensive_function("a", param2="b")
        assert call_count == 1  # Function not called again
        assert result1 == result2
        
        # Call with different params should execute function
        result3 = await expensive_function("x", param2="y")
        assert call_count == 2
        assert "result_x_y_2" == result3
    
    @pytest.mark.asyncio
    async def test_smart_cache_with_sync_function(self, cache_manager):
        """Test SmartCache with synchronous function"""
        call_count = 0
        
        @SmartCache(cache_manager, "sync_cache")
        def sync_function(value):
            nonlocal call_count
            call_count += 1
            return f"sync_result_{value}_{call_count}"
        
        # First call should execute function
        result1 = await sync_function("test")
        assert call_count == 1
        assert "sync_result_test_1" == result1
        
        # Second call should use cache
        result2 = await sync_function("test")
        assert call_count == 1
        assert result1 == result2


@pytest.mark.asyncio
async def test_cache_manager_with_redis_config():
    """Test cache manager initialization with Redis config"""
    redis_config = {
        'memory_cache_size': 100,
        'memory_cache_ttl': 300,
        'use_redis': True,
        'redis_host': 'localhost',
        'redis_port': 6379,
        'redis_db': 0
    }
    
    with patch('cache_manager.redis') as mock_redis:
        # Mock Redis client
        mock_redis_client = AsyncMock()
        mock_redis_client.ping = AsyncMock(side_effect=Exception("Redis not available"))
        mock_redis.Redis.return_value = mock_redis_client
        
        manager = CacheManager(redis_config)
        await manager.initialize()
        
        # Should fallback gracefully when Redis is not available
        assert manager.redis_client is None
        
        await manager.close()


@pytest.mark.asyncio
async def test_cache_with_complex_data_types(cache_manager):
    """Test caching with complex data structures"""
    complex_data = {
        "list": [1, 2, 3, {"nested": "value"}],
        "dict": {"key": "value", "nested": {"deep": "data"}},
        "string": "test string",
        "number": 42,
        "boolean": True,
        "null": None
    }
    
    # Set complex data
    await cache_manager.set("complex_key", complex_data, "test")
    
    # Get and verify
    result = await cache_manager.get("complex_key", "test")
    
    assert result is not None
    assert result["list"] == [1, 2, 3, {"nested": "value"}]
    assert result["dict"]["nested"]["deep"] == "data"
    assert result["string"] == "test string"
    assert result["number"] == 42
    assert result["boolean"] is True
    assert result["null"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])