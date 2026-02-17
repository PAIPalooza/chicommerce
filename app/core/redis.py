"""
Redis connection configuration and dependency injection.

This module provides Redis client initialization and dependency
injection for FastAPI endpoints.
"""
import logging
from typing import Optional, AsyncGenerator

import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisConnectionManager:
    """
    Manages Redis connections with proper lifecycle handling.

    This class implements a singleton pattern for Redis connections
    to ensure efficient connection pooling and reuse.
    """

    _instance: Optional[Redis] = None

    @classmethod
    async def get_redis_client(cls) -> Redis:
        """
        Get or create Redis client instance.

        Returns:
            Redis: Async Redis client instance
        """
        if cls._instance is None:
            try:
                cls._instance = await redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                    max_connections=10,
                )
                logger.info(f"Redis client connected to {settings.REDIS_URL}")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {str(e)}")
                raise

        return cls._instance

    @classmethod
    async def close_redis_client(cls) -> None:
        """
        Close Redis client connection.

        Should be called during application shutdown.
        """
        if cls._instance is not None:
            await cls._instance.close()
            cls._instance = None
            logger.info("Redis client connection closed")


async def get_redis() -> AsyncGenerator[Redis, None]:
    """
    FastAPI dependency for Redis client.

    Yields:
        Redis: Async Redis client instance

    Example:
        @router.get("/")
        async def endpoint(redis: Redis = Depends(get_redis)):
            await redis.set("key", "value")
    """
    client = await RedisConnectionManager.get_redis_client()
    try:
        yield client
    except Exception as e:
        logger.error(f"Error in Redis operation: {str(e)}")
        raise


async def init_redis() -> None:
    """
    Initialize Redis connection on application startup.

    Should be called in FastAPI startup event handler.
    """
    try:
        await RedisConnectionManager.get_redis_client()
        logger.info("Redis initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {str(e)}")
        raise


async def close_redis() -> None:
    """
    Close Redis connection on application shutdown.

    Should be called in FastAPI shutdown event handler.
    """
    await RedisConnectionManager.close_redis_client()
