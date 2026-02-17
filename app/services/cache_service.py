"""
Redis caching service with metrics collection.

This module provides a comprehensive caching service with:
- Configurable TTL (Time To Live)
- Cache key generation utilities
- Cache invalidation patterns
- Metrics collection for monitoring cache effectiveness
"""
import json
import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

from redis.asyncio import Redis

from app.core.redis import RedisConnectionManager

logger = logging.getLogger(__name__)


@dataclass
class CacheMetrics:
    """
    Tracks cache performance metrics.

    Attributes:
        hits: Number of cache hits
        misses: Number of cache misses
    """
    hits: int = 0
    misses: int = 0

    @property
    def total_requests(self) -> int:
        """Calculate total cache requests."""
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        """
        Calculate cache hit rate.

        Returns:
            float: Hit rate between 0.0 and 1.0
        """
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests

    def increment_hits(self) -> None:
        """Increment cache hit counter."""
        self.hits += 1

    def increment_misses(self) -> None:
        """Increment cache miss counter."""
        self.misses += 1

    def reset(self) -> None:
        """Reset all metrics to zero."""
        self.hits = 0
        self.misses = 0


class CacheService:
    """
    Redis-based caching service with metrics.

    This service provides async cache operations with automatic
    JSON serialization/deserialization and metrics tracking.

    Example:
        cache = CacheService(default_ttl=60)
        await cache.set("products:list", products_data)
        cached_data = await cache.get("products:list")
        metrics = cache.get_metrics()
    """

    def __init__(self, default_ttl: int = 60):
        """
        Initialize cache service.

        Args:
            default_ttl: Default time to live in seconds (default: 60)
        """
        self.default_ttl = default_ttl
        self.metrics = CacheMetrics()
        self.redis: Optional[Redis] = None

    async def _get_redis(self) -> Redis:
        """
        Get Redis client instance.

        Returns:
            Redis: Async Redis client
        """
        if self.redis is None:
            self.redis = await RedisConnectionManager.get_redis_client()
        return self.redis

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or error occurred
        """
        try:
            redis = await self._get_redis()
            value = await redis.get(key)

            if value is None:
                self.metrics.increment_misses()
                logger.debug(f"Cache miss for key: {key}")
                return None

            self.metrics.increment_hits()
            logger.debug(f"Cache hit for key: {key}")

            # Deserialize JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to deserialize cached value for key {key}: {str(e)}")
                # Delete corrupted cache entry
                await self.delete(key)
                return None

        except Exception as e:
            logger.error(f"Error getting cache key {key}: {str(e)}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (uses default_ttl if not provided)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            redis = await self._get_redis()
            ttl = ttl or self.default_ttl

            # Serialize to JSON
            serialized_value = json.dumps(value)

            # Use setex for atomic set with expiration
            await redis.setex(key, ttl, serialized_value)
            logger.debug(f"Set cache key: {key} with TTL: {ttl}s")
            return True

        except Exception as e:
            logger.error(f"Error setting cache key {key}: {str(e)}")
            return False

    async def delete(self, *keys: str) -> int:
        """
        Delete one or more keys from cache.

        Args:
            *keys: One or more cache keys to delete

        Returns:
            int: Number of keys deleted
        """
        try:
            redis = await self._get_redis()
            deleted_count = await redis.delete(*keys)
            logger.debug(f"Deleted {deleted_count} cache keys")
            return deleted_count

        except Exception as e:
            logger.error(f"Error deleting cache keys: {str(e)}")
            return 0

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern.

        Args:
            pattern: Redis key pattern (e.g., "product*", "templates:*")

        Returns:
            int: Number of keys invalidated

        Example:
            # Invalidate all product-related caches
            await cache.invalidate_pattern("product*")
        """
        try:
            redis = await self._get_redis()

            # Find all keys matching the pattern
            keys = await redis.keys(pattern)

            if not keys:
                logger.debug(f"No keys found for pattern: {pattern}")
                return 0

            # Convert bytes to strings if needed
            str_keys = [k.decode() if isinstance(k, bytes) else k for k in keys]

            # Delete all matching keys
            deleted_count = await redis.delete(*str_keys)
            logger.info(f"Invalidated {deleted_count} cache keys matching pattern: {pattern}")
            return deleted_count

        except Exception as e:
            logger.error(f"Error invalidating pattern {pattern}: {str(e)}")
            return 0

    async def exists(self, *keys: str) -> int:
        """
        Check if one or more keys exist in cache.

        Args:
            *keys: One or more cache keys to check

        Returns:
            int: Number of existing keys
        """
        try:
            redis = await self._get_redis()
            return await redis.exists(*keys)

        except Exception as e:
            logger.error(f"Error checking key existence: {str(e)}")
            return 0

    async def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration time for a key.

        Args:
            key: Cache key
            ttl: Time to live in seconds

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            redis = await self._get_redis()
            result = await redis.expire(key, ttl)
            return bool(result)

        except Exception as e:
            logger.error(f"Error setting expiration for key {key}: {str(e)}")
            return False

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current cache metrics.

        Returns:
            Dictionary containing cache performance metrics
        """
        return {
            "hits": self.metrics.hits,
            "misses": self.metrics.misses,
            "total_requests": self.metrics.total_requests,
            "hit_rate": self.metrics.hit_rate,
        }

    def reset_metrics(self) -> None:
        """Reset cache metrics to zero."""
        self.metrics.reset()
        logger.info("Cache metrics reset")


def generate_cache_key(prefix: str, **kwargs) -> str:
    """
    Generate a consistent cache key from prefix and parameters.

    Args:
        prefix: Key prefix (e.g., "products", "template")
        **kwargs: Key-value pairs to include in the cache key

    Returns:
        str: Generated cache key

    Example:
        >>> generate_cache_key("products", skip=0, limit=100, active_only=True)
        'products:skip=0:limit=100:active_only=True'

        >>> generate_cache_key("product", product_id="123e4567-...")
        'product:product_id=123e4567-...'
    """
    # Sort parameters for consistency
    sorted_params = sorted(kwargs.items())

    # Build key parts
    parts = [prefix]
    for key, value in sorted_params:
        if value is not None:
            parts.append(f"{key}={value}")

    return ":".join(parts)


# Global cache service instance with 60-second TTL
cache_service = CacheService(default_ttl=60)


async def get_cache_service() -> CacheService:
    """
    FastAPI dependency for cache service.

    Returns:
        CacheService: Global cache service instance

    Example:
        @router.get("/")
        async def endpoint(cache: CacheService = Depends(get_cache_service)):
            await cache.set("key", "value")
    """
    return cache_service
