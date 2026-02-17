"""
Tests for Redis caching service using BDD/TDD approach.

This module tests the caching service functionality including:
- Basic cache operations (set, get, delete)
- Cache key generation
- TTL (Time To Live) configuration
- Cache invalidation patterns
- Metrics collection for cache hit/miss rates
"""
import pytest
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from app.services.cache_service import (
    CacheService,
    CacheMetrics,
    generate_cache_key,
)


class TestCacheService:
    """Test suite for CacheService class."""

    def describe_initialization(self):
        """Tests for cache service initialization."""

        def it_initializes_with_default_ttl(self):
            """Should initialize cache service with default TTL of 60 seconds."""
            cache_service = CacheService()
            assert cache_service.default_ttl == 60

        def it_initializes_with_custom_ttl(self):
            """Should initialize cache service with custom TTL."""
            cache_service = CacheService(default_ttl=120)
            assert cache_service.default_ttl == 120

        def it_initializes_metrics_tracker(self):
            """Should initialize metrics tracker for cache operations."""
            cache_service = CacheService()
            assert cache_service.metrics is not None
            assert cache_service.metrics.hits == 0
            assert cache_service.metrics.misses == 0

    def describe_cache_key_generation(self):
        """Tests for cache key generation."""

        def it_generates_key_for_product_list(self):
            """Should generate consistent cache key for product list."""
            key = generate_cache_key("products", skip=0, limit=100, active_only=True)
            expected = "products:skip=0:limit=100:active_only=True"
            assert key == expected

        def it_generates_key_for_product_detail(self):
            """Should generate cache key for single product."""
            product_id = "123e4567-e89b-12d3-a456-426614174000"
            key = generate_cache_key("product", product_id=product_id)
            expected = f"product:product_id={product_id}"
            assert key == expected

        def it_generates_key_for_template_list(self):
            """Should generate cache key for template list by product."""
            product_id = "123e4567-e89b-12d3-a456-426614174000"
            key = generate_cache_key("templates", product_id=product_id)
            expected = f"templates:product_id={product_id}"
            assert key == expected

        def it_handles_none_values_in_key_generation(self):
            """Should handle None values when generating cache keys."""
            key = generate_cache_key("products", skip=0, limit=None, active_only=True)
            # None values should be converted to string 'None'
            assert "limit=None" in key or "limit" not in key

    @pytest.mark.asyncio
    async def describe_cache_get_operations(self):
        """Tests for cache get operations."""

        async def it_returns_none_for_cache_miss(self):
            """Should return None when key is not in cache."""
            with patch('redis.asyncio.Redis') as mock_redis:
                mock_client = AsyncMock()
                mock_client.get.return_value = None
                mock_redis.from_url.return_value = mock_client

                cache_service = CacheService()
                cache_service.redis = mock_client

                result = await cache_service.get("nonexistent_key")
                assert result is None
                assert cache_service.metrics.misses == 1

        async def it_returns_cached_value_for_cache_hit(self):
            """Should return cached value and increment hit counter."""
            cached_data = {"id": "123", "name": "Test Product"}

            with patch('redis.asyncio.Redis') as mock_redis:
                mock_client = AsyncMock()
                mock_client.get.return_value = json.dumps(cached_data).encode()
                mock_redis.from_url.return_value = mock_client

                cache_service = CacheService()
                cache_service.redis = mock_client

                result = await cache_service.get("test_key")
                assert result == cached_data
                assert cache_service.metrics.hits == 1

        async def it_handles_json_decode_errors_gracefully(self):
            """Should return None and log error for invalid JSON."""
            with patch('redis.asyncio.Redis') as mock_redis:
                mock_client = AsyncMock()
                mock_client.get.return_value = b"invalid json {{"
                mock_redis.from_url.return_value = mock_client

                cache_service = CacheService()
                cache_service.redis = mock_client

                result = await cache_service.get("test_key")
                assert result is None

    @pytest.mark.asyncio
    async def describe_cache_set_operations(self):
        """Tests for cache set operations."""

        async def it_sets_value_with_default_ttl(self):
            """Should set cache value with default TTL of 60 seconds."""
            with patch('redis.asyncio.Redis') as mock_redis:
                mock_client = AsyncMock()
                mock_client.setex.return_value = True
                mock_redis.from_url.return_value = mock_client

                cache_service = CacheService(default_ttl=60)
                cache_service.redis = mock_client

                data = {"id": "123", "name": "Test Product"}
                await cache_service.set("test_key", data)

                # Verify setex was called with correct TTL
                mock_client.setex.assert_called_once()
                call_args = mock_client.setex.call_args
                assert call_args[0][0] == "test_key"
                assert call_args[0][1] == 60

        async def it_sets_value_with_custom_ttl(self):
            """Should set cache value with custom TTL."""
            with patch('redis.asyncio.Redis') as mock_redis:
                mock_client = AsyncMock()
                mock_client.setex.return_value = True
                mock_redis.from_url.return_value = mock_client

                cache_service = CacheService()
                cache_service.redis = mock_client

                data = {"id": "123", "name": "Test Product"}
                await cache_service.set("test_key", data, ttl=120)

                # Verify setex was called with custom TTL
                call_args = mock_client.setex.call_args
                assert call_args[0][1] == 120

        async def it_serializes_data_to_json(self):
            """Should serialize complex data structures to JSON."""
            with patch('redis.asyncio.Redis') as mock_redis:
                mock_client = AsyncMock()
                mock_client.setex.return_value = True
                mock_redis.from_url.return_value = mock_client

                cache_service = CacheService()
                cache_service.redis = mock_client

                data = {
                    "id": "123",
                    "name": "Test Product",
                    "price": 19.99,
                    "active": True,
                    "tags": ["new", "featured"]
                }
                await cache_service.set("test_key", data)

                # Verify data was JSON serialized
                call_args = mock_client.setex.call_args
                json_data = call_args[0][2]
                assert isinstance(json_data, str)
                assert json.loads(json_data) == data

    @pytest.mark.asyncio
    async def describe_cache_delete_operations(self):
        """Tests for cache delete operations."""

        async def it_deletes_single_key(self):
            """Should delete a single cache key."""
            with patch('redis.asyncio.Redis') as mock_redis:
                mock_client = AsyncMock()
                mock_client.delete.return_value = 1
                mock_redis.from_url.return_value = mock_client

                cache_service = CacheService()
                cache_service.redis = mock_client

                await cache_service.delete("test_key")
                mock_client.delete.assert_called_once_with("test_key")

        async def it_deletes_multiple_keys(self):
            """Should delete multiple cache keys."""
            with patch('redis.asyncio.Redis') as mock_redis:
                mock_client = AsyncMock()
                mock_client.delete.return_value = 3
                mock_redis.from_url.return_value = mock_client

                cache_service = CacheService()
                cache_service.redis = mock_client

                await cache_service.delete("key1", "key2", "key3")
                mock_client.delete.assert_called_once_with("key1", "key2", "key3")

    @pytest.mark.asyncio
    async def describe_cache_invalidation_patterns(self):
        """Tests for cache invalidation patterns."""

        async def it_invalidates_product_cache_pattern(self):
            """Should invalidate all product-related cache keys."""
            with patch('redis.asyncio.Redis') as mock_redis:
                mock_client = AsyncMock()
                mock_client.keys.return_value = [
                    b"products:*",
                    b"product:123",
                    b"product:456"
                ]
                mock_client.delete.return_value = 3
                mock_redis.from_url.return_value = mock_client

                cache_service = CacheService()
                cache_service.redis = mock_client

                await cache_service.invalidate_pattern("product*")

                # Verify pattern search and deletion
                mock_client.keys.assert_called_once_with("product*")

        async def it_invalidates_template_cache_pattern(self):
            """Should invalidate all template-related cache keys."""
            with patch('redis.asyncio.Redis') as mock_redis:
                mock_client = AsyncMock()
                product_id = "123e4567-e89b-12d3-a456-426614174000"
                mock_client.keys.return_value = [
                    f"templates:product_id={product_id}".encode(),
                    f"template:456".encode()
                ]
                mock_client.delete.return_value = 2
                mock_redis.from_url.return_value = mock_client

                cache_service = CacheService()
                cache_service.redis = mock_client

                await cache_service.invalidate_pattern(f"template*{product_id}*")

                mock_client.keys.assert_called_once()

    @pytest.mark.asyncio
    async def describe_cache_metrics(self):
        """Tests for cache metrics collection."""

        async def it_tracks_hit_rate(self):
            """Should track cache hit rate correctly."""
            with patch('redis.asyncio.Redis') as mock_redis:
                mock_client = AsyncMock()
                # Simulate 3 hits and 2 misses
                mock_client.get.side_effect = [
                    json.dumps({"data": "1"}).encode(),  # hit
                    json.dumps({"data": "2"}).encode(),  # hit
                    None,  # miss
                    json.dumps({"data": "3"}).encode(),  # hit
                    None,  # miss
                ]
                mock_redis.from_url.return_value = mock_client

                cache_service = CacheService()
                cache_service.redis = mock_client

                await cache_service.get("key1")
                await cache_service.get("key2")
                await cache_service.get("key3")
                await cache_service.get("key4")
                await cache_service.get("key5")

                metrics = cache_service.get_metrics()
                assert metrics["hits"] == 3
                assert metrics["misses"] == 2
                assert metrics["total_requests"] == 5
                assert metrics["hit_rate"] == 0.6  # 3/5

        async def it_handles_zero_requests_for_hit_rate(self):
            """Should return 0.0 hit rate when no requests made."""
            cache_service = CacheService()
            metrics = cache_service.get_metrics()
            assert metrics["hit_rate"] == 0.0
            assert metrics["total_requests"] == 0

        async def it_resets_metrics(self):
            """Should reset metrics to zero."""
            with patch('redis.asyncio.Redis') as mock_redis:
                mock_client = AsyncMock()
                mock_client.get.side_effect = [
                    json.dumps({"data": "1"}).encode(),
                    None,
                ]
                mock_redis.from_url.return_value = mock_client

                cache_service = CacheService()
                cache_service.redis = mock_client

                await cache_service.get("key1")
                await cache_service.get("key2")

                assert cache_service.metrics.hits == 1
                assert cache_service.metrics.misses == 1

                cache_service.reset_metrics()
                assert cache_service.metrics.hits == 0
                assert cache_service.metrics.misses == 0


class TestCacheMetrics:
    """Test suite for CacheMetrics class."""

    def describe_metrics_calculation(self):
        """Tests for metrics calculations."""

        def it_calculates_total_requests(self):
            """Should calculate total requests as sum of hits and misses."""
            metrics = CacheMetrics()
            metrics.hits = 10
            metrics.misses = 5

            assert metrics.total_requests == 15

        def it_calculates_hit_rate(self):
            """Should calculate hit rate as percentage of hits."""
            metrics = CacheMetrics()
            metrics.hits = 75
            metrics.misses = 25

            assert metrics.hit_rate == 0.75

        def it_handles_zero_total_requests(self):
            """Should return 0.0 hit rate when no requests."""
            metrics = CacheMetrics()
            metrics.hits = 0
            metrics.misses = 0

            assert metrics.hit_rate == 0.0

        def it_increments_hits(self):
            """Should increment hit counter."""
            metrics = CacheMetrics()
            initial_hits = metrics.hits

            metrics.increment_hits()
            assert metrics.hits == initial_hits + 1

        def it_increments_misses(self):
            """Should increment miss counter."""
            metrics = CacheMetrics()
            initial_misses = metrics.misses

            metrics.increment_misses()
            assert metrics.misses == initial_misses + 1


class TestCacheKeyGeneration:
    """Test suite for cache key generation utility."""

    def describe_key_format(self):
        """Tests for cache key format."""

        def it_generates_key_with_prefix(self):
            """Should generate key starting with prefix."""
            key = generate_cache_key("products")
            assert key.startswith("products:")

        def it_generates_key_with_sorted_params(self):
            """Should generate key with sorted parameters for consistency."""
            key1 = generate_cache_key("products", skip=0, limit=100)
            key2 = generate_cache_key("products", limit=100, skip=0)

            # Both should generate the same key
            assert key1 == key2

        def it_generates_key_with_uuid(self):
            """Should handle UUID parameters."""
            product_id = "123e4567-e89b-12d3-a456-426614174000"
            key = generate_cache_key("product", product_id=product_id)

            assert product_id in key

        def it_generates_key_with_boolean(self):
            """Should handle boolean parameters."""
            key = generate_cache_key("products", active_only=True)

            assert "active_only=True" in key
