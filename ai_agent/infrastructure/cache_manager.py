import asyncio
import json
import time
import hashlib
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import aiofiles
import redis.asyncio as redis
from cachetools import TTLCache
from pathlib import Path
import structlog

logger = structlog.get_logger(__name__)


class CacheManager:
    """Advanced caching system with multiple storage backends"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.memory_cache = TTLCache(
            maxsize=config.get('memory_cache_size', 1000),
            ttl=config.get('memory_cache_ttl', 300)  # 5 minutes
        )
        self.redis_client = None
        self.file_cache_dir = Path(config.get('file_cache_dir', './cache'))
        self.file_cache_dir.mkdir(exist_ok=True)
        
        # Cache configuration
        self.cache_ttl = {
            'confluence': config.get('confluence_cache_ttl', 1800),  # 30 minutes
            'jira': config.get('jira_cache_ttl', 600),  # 10 minutes
            'code': config.get('code_cache_ttl', 3600),  # 1 hour
            'ai_response': config.get('ai_cache_ttl', 7200),  # 2 hours
        }
    
    async def initialize(self):
        """Initialize cache backends"""
        if self.config.get('use_redis', False):
            try:
                self.redis_client = redis.Redis(
                    host=self.config.get('redis_host', 'localhost'),
                    port=self.config.get('redis_port', 6379),
                    db=self.config.get('redis_db', 0),
                    password=self.config.get('redis_password'),
                    decode_responses=True
                )
                await self.redis_client.ping()
                logger.info("Redis cache initialized")
            except Exception as e:
                logger.warning(f"Redis not available, using memory cache: {e}")
                self.redis_client = None
    
    async def get(self, key: str, cache_type: str = 'default') -> Optional[Any]:
        """Get value from cache with fallback strategy"""
        cache_key = self._generate_key(key, cache_type)
        
        # Try memory cache first
        if cache_key in self.memory_cache:
            logger.debug(f"Cache hit (memory): {cache_key}")
            return self.memory_cache[cache_key]
        
        # Try Redis cache
        if self.redis_client:
            try:
                value = await self.redis_client.get(cache_key)
                if value:
                    data = json.loads(value)
                    # Update memory cache
                    self.memory_cache[cache_key] = data
                    logger.debug(f"Cache hit (redis): {cache_key}")
                    return data
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")
        
        # Try file cache
        file_path = self.file_cache_dir / f"{cache_key}.json"
        if file_path.exists():
            try:
                async with aiofiles.open(file_path, 'r') as f:
                    content = await f.read()
                    data = json.loads(content)
                    
                    # Check if expired
                    if data.get('expires_at', 0) > time.time():
                        cached_value = data['value']
                        # Update higher level caches
                        self.memory_cache[cache_key] = cached_value
                        if self.redis_client:
                            await self._set_redis(cache_key, cached_value, cache_type)
                        logger.debug(f"Cache hit (file): {cache_key}")
                        return cached_value
                    else:
                        # Remove expired file
                        file_path.unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"File cache error: {e}")
        
        logger.debug(f"Cache miss: {cache_key}")
        return None
    
    async def set(self, key: str, value: Any, cache_type: str = 'default') -> None:
        """Set value in all available cache layers"""
        cache_key = self._generate_key(key, cache_type)
        ttl = self.cache_ttl.get(cache_type, 300)
        
        # Memory cache
        self.memory_cache[cache_key] = value
        
        # Redis cache
        if self.redis_client:
            await self._set_redis(cache_key, value, cache_type)
        
        # File cache (for persistence)
        await self._set_file(cache_key, value, ttl)
        
        logger.debug(f"Cache set: {cache_key}")
    
    async def delete(self, key: str, cache_type: str = 'default') -> None:
        """Delete value from all cache layers"""
        cache_key = self._generate_key(key, cache_type)
        
        # Memory cache
        self.memory_cache.pop(cache_key, None)
        
        # Redis cache
        if self.redis_client:
            try:
                await self.redis_client.delete(cache_key)
            except Exception as e:
                logger.warning(f"Redis delete error: {e}")
        
        # File cache
        file_path = self.file_cache_dir / f"{cache_key}.json"
        file_path.unlink(missing_ok=True)
        
        logger.debug(f"Cache deleted: {cache_key}")
    
    async def clear(self, cache_type: Optional[str] = None) -> None:
        """Clear cache entries"""
        if cache_type:
            # Clear specific cache type
            keys_to_remove = [k for k in self.memory_cache.keys() if cache_type in k]
            for key in keys_to_remove:
                self.memory_cache.pop(key, None)
        else:
            # Clear all
            self.memory_cache.clear()
        
        if self.redis_client and cache_type:
            try:
                pattern = f"*{cache_type}*"
                keys = await self.redis_client.keys(pattern)
                if keys:
                    await self.redis_client.delete(*keys)
            except Exception as e:
                logger.warning(f"Redis clear error: {e}")
        
        # Clear file cache
        if cache_type:
            for file_path in self.file_cache_dir.glob(f"*{cache_type}*.json"):
                file_path.unlink(missing_ok=True)
        else:
            for file_path in self.file_cache_dir.glob("*.json"):
                file_path.unlink(missing_ok=True)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = {
            'memory_cache': {
                'size': len(self.memory_cache),
                'maxsize': self.memory_cache.maxsize,
                'hits': getattr(self.memory_cache, 'hits', 0),
                'misses': getattr(self.memory_cache, 'misses', 0)
            }
        }
        
        if self.redis_client:
            try:
                info = await self.redis_client.info('memory')
                stats['redis'] = {
                    'used_memory': info.get('used_memory_human'),
                    'connected_clients': info.get('connected_clients')
                }
            except Exception as e:
                stats['redis'] = {'error': str(e)}
        
        # File cache stats
        file_count = len(list(self.file_cache_dir.glob("*.json")))
        total_size = sum(f.stat().st_size for f in self.file_cache_dir.glob("*.json"))
        stats['file_cache'] = {
            'file_count': file_count,
            'total_size_mb': round(total_size / 1024 / 1024, 2)
        }
        
        return stats
    
    def _generate_key(self, key: str, cache_type: str) -> str:
        """Generate cache key with type prefix and hash"""
        key_hash = hashlib.md5(key.encode()).hexdigest()[:12]
        return f"agent:{cache_type}:{key_hash}"
    
    async def _set_redis(self, cache_key: str, value: Any, cache_type: str) -> None:
        """Set value in Redis with TTL"""
        try:
            ttl = self.cache_ttl.get(cache_type, 300)
            await self.redis_client.setex(
                cache_key, 
                ttl, 
                json.dumps(value, default=str)
            )
        except Exception as e:
            logger.warning(f"Redis set error: {e}")
    
    async def _set_file(self, cache_key: str, value: Any, ttl: int) -> None:
        """Set value in file cache with expiration"""
        try:
            file_path = self.file_cache_dir / f"{cache_key}.json"
            cache_data = {
                'value': value,
                'created_at': time.time(),
                'expires_at': time.time() + ttl
            }
            async with aiofiles.open(file_path, 'w') as f:
                await f.write(json.dumps(cache_data, default=str, indent=2))
        except Exception as e:
            logger.warning(f"File cache set error: {e}")
    
    async def cleanup_expired(self) -> None:
        """Cleanup expired file cache entries"""
        current_time = time.time()
        for file_path in self.file_cache_dir.glob("*.json"):
            try:
                async with aiofiles.open(file_path, 'r') as f:
                    content = await f.read()
                    data = json.loads(content)
                    if data.get('expires_at', 0) <= current_time:
                        file_path.unlink()
            except Exception:
                # Remove corrupted files
                file_path.unlink(missing_ok=True)
    
    async def close(self) -> None:
        """Close cache connections"""
        if self.redis_client:
            await self.redis_client.close()


class SmartCache:
    """Decorator for automatic caching of async functions"""
    
    def __init__(self, cache_manager: CacheManager, cache_type: str = 'default', ttl: Optional[int] = None):
        self.cache_manager = cache_manager
        self.cache_type = cache_type
        self.ttl = ttl
    
    def __call__(self, func):
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_parts = [func.__name__]
            key_parts.extend([str(arg) for arg in args])
            key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
            cache_key = "|".join(key_parts)
            
            # Try to get from cache
            cached_result = await self.cache_manager.get(cache_key, self.cache_type)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await self.cache_manager.set(cache_key, result, self.cache_type)
            
            return result
        
        return wrapper