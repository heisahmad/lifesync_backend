import redis
import json
from typing import Any, Optional, Callable
from app.core.config import settings
from datetime import timedelta
import functools

class RedisCache:
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL)
        self.default_expiry = timedelta(hours=1)

    async def set_json(self, key: str, value: Any, expiry: Optional[timedelta] = None) -> None:
        """Store JSON serializable data with optional expiry"""
        serialized = json.dumps(value)
        await self.set_key(key, serialized, expiry or self.default_expiry)

    async def get_json(self, key: str) -> Optional[Any]:
        """Retrieve and deserialize JSON data"""
        value = await self.get_key(key)
        if value:
            return json.loads(value)
        return None

    async def set_key(self, key: str, value: str, expiry: timedelta) -> None:
        """Set key with expiration"""
        self.redis_client.setex(
            key,
            int(expiry.total_seconds()),
            value
        )

    async def get_key(self, key: str) -> Optional[str]:
        """Get value by key"""
        return self.redis_client.get(key)

    async def delete_key(self, key: str) -> None:
        """Delete a key"""
        self.redis_client.delete(key)

    async def set_hash(self, name: str, mapping: dict, expiry: Optional[timedelta] = None) -> None:
        """Store hash data with optional expiry"""
        self.redis_client.hmset(name, mapping)
        if expiry:
            self.redis_client.expire(name, int(expiry.total_seconds()))

    async def get_hash(self, name: str) -> dict:
        """Get all fields in a hash"""
        return self.redis_client.hgetall(name)

    async def invalidate_pattern(self, pattern: str) -> None:
        """Delete all keys matching a pattern"""
        for key in self.redis_client.scan_iter(pattern):
            self.redis_client.delete(key)

    def cache(self, expiration: int = 3600):
        """Decorator for caching function results"""
        def decorator(func: Callable):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                # Create cache key from function name and arguments
                key = f"cache:{func.__name__}:{str(args)}:{str(kwargs)}"
                
                # Try to get from cache
                cached = await self.get_json(key)
                if cached is not None:
                    return cached
                
                # If not in cache, execute function
                result = await func(*args, **kwargs)
                
                # Cache the result
                await self.set_json(key, result, timedelta(seconds=expiration))
                
                return result
            return wrapper
        return decorator

# Create a global Redis cache instance
redis_cache = RedisCache()
