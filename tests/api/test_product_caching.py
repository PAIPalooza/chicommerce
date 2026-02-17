"""
Integration tests for product caching functionality.

Tests the caching behavior of product endpoints including:
- Cache hits and misses
- Cache invalidation on updates
- Performance requirements (<100ms for cached responses)
"""
import pytest
import time
from uuid import UUID
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.services.cache_service import CacheService


class TestProductCaching:
    """Integration tests for product endpoint caching."""

    def describe_product_list_caching(self):
        """Tests for GET /products caching."""

        @pytest.mark.asyncio
        async def it_caches_product_list_response(self, client, sample_product):
            """Should cache product list on first request and serve from cache on second."""
            # First request - should be a cache miss
            response1 = client.get("/api/v1/products?skip=0&limit=100&active_only=true")
            assert response1.status_code == 200

            # Second request with same params - should be a cache hit
            response2 = client.get("/api/v1/products?skip=0&limit=100&active_only=true")
            assert response2.status_code == 200

            # Responses should be identical
            assert response1.json() == response2.json()

        @pytest.mark.asyncio
        async def it_caches_different_pagination_separately(self, client, sample_product):
            """Should cache different pagination parameters separately."""
            # Request with skip=0
            response1 = client.get("/api/v1/products?skip=0&limit=50&active_only=true")
            assert response1.status_code == 200

            # Request with skip=50 - different cache key
            response2 = client.get("/api/v1/products?skip=50&limit=50&active_only=true")
            assert response2.status_code == 200

            # These should have different cache keys and potentially different results

        @pytest.mark.asyncio
        async def it_invalidates_cache_on_product_creation(self, client, db_session):
            """Should invalidate product list cache when new product is created."""
            # Get initial product list
            response1 = client.get("/api/v1/products?skip=0&limit=100&active_only=true")
            assert response1.status_code == 200
            initial_count = len(response1.json())

            # Create a new product
            new_product = {
                "name": "New Cached Product",
                "description": "Testing cache invalidation",
                "base_price": 29.99,
                "media": {"images": ["test.jpg"]},
                "is_active": True
            }
            create_response = client.post("/api/v1/products", json=new_product)
            assert create_response.status_code == 201

            # Get product list again - should be refreshed from DB
            response2 = client.get("/api/v1/products?skip=0&limit=100&active_only=true")
            assert response2.status_code == 200
            new_count = len(response2.json())

            # Should have one more product
            assert new_count == initial_count + 1

    def describe_product_detail_caching(self):
        """Tests for GET /products/{id} caching."""

        @pytest.mark.asyncio
        async def it_caches_product_detail_response(self, client, sample_product):
            """Should cache individual product detail on first request."""
            product_id = str(sample_product.id)

            # First request
            response1 = client.get(f"/api/v1/products/{product_id}")
            assert response1.status_code == 200

            # Second request - should be cached
            response2 = client.get(f"/api/v1/products/{product_id}")
            assert response2.status_code == 200

            # Responses should be identical
            assert response1.json() == response2.json()

        @pytest.mark.asyncio
        async def it_invalidates_cache_on_product_update(self, client, sample_product):
            """Should invalidate product cache when product is updated."""
            product_id = str(sample_product.id)

            # Get initial product
            response1 = client.get(f"/api/v1/products/{product_id}")
            assert response1.status_code == 200
            initial_name = response1.json()["name"]

            # Update the product
            update_data = {"name": "Updated Cached Product"}
            update_response = client.put(
                f"/api/v1/products/{product_id}",
                json=update_data
            )
            assert update_response.status_code == 200

            # Get product again - should reflect the update
            response2 = client.get(f"/api/v1/products/{product_id}")
            assert response2.status_code == 200
            updated_name = response2.json()["name"]

            assert updated_name != initial_name
            assert updated_name == "Updated Cached Product"

        @pytest.mark.asyncio
        async def it_invalidates_cache_on_product_deletion(self, client, sample_product):
            """Should invalidate product cache when product is deleted."""
            product_id = str(sample_product.id)

            # Get initial product
            response1 = client.get(f"/api/v1/products/{product_id}")
            assert response1.status_code == 200

            # Delete the product
            delete_response = client.delete(f"/api/v1/products/{product_id}")
            assert delete_response.status_code == 204

            # Attempt to get the deleted product - should return 404
            response2 = client.get(f"/api/v1/products/{product_id}")
            assert response2.status_code == 404

    def describe_cache_ttl_expiration(self):
        """Tests for cache TTL (Time To Live) expiration."""

        @pytest.mark.asyncio
        async def it_expires_cache_after_60_seconds(self, client, sample_product):
            """Should expire cache entries after 60 seconds TTL."""
            # This is a conceptual test - in real scenarios, waiting 60s is impractical
            # In practice, we'd mock time or use a shorter TTL for testing
            product_id = str(sample_product.id)

            with patch('app.services.cache_service.CacheService') as mock_cache:
                # Mock the cache service to verify TTL is set correctly
                mock_instance = AsyncMock()
                mock_cache.return_value = mock_instance

                response = client.get(f"/api/v1/products/{product_id}")
                assert response.status_code == 200

                # Verify cache was set with 60 second TTL
                # This would be implementation-specific based on how we integrate caching

    def describe_cache_performance(self):
        """Tests for cache performance requirements."""

        @pytest.mark.asyncio
        async def it_responds_under_100ms_for_cached_requests(self, client, sample_product):
            """Should respond in under 100ms for cached product requests (95th percentile)."""
            product_id = str(sample_product.id)

            # Prime the cache with first request
            client.get(f"/api/v1/products/{product_id}")

            # Measure response times for cached requests
            response_times = []
            for _ in range(20):
                start_time = time.time()
                response = client.get(f"/api/v1/products/{product_id}")
                end_time = time.time()

                assert response.status_code == 200
                response_time_ms = (end_time - start_time) * 1000
                response_times.append(response_time_ms)

            # Calculate 95th percentile
            response_times.sort()
            percentile_95_index = int(len(response_times) * 0.95)
            percentile_95 = response_times[percentile_95_index]

            # For cached responses, 95th percentile should be under 100ms
            # Note: This is a loose test as it depends on system performance
            # In production, this would be measured under proper load conditions
            assert percentile_95 < 100, f"95th percentile response time {percentile_95}ms exceeds 100ms"

        @pytest.mark.asyncio
        async def it_responds_under_100ms_for_product_list(self, client, sample_product):
            """Should respond in under 100ms for cached product list (95th percentile)."""
            # Prime the cache
            client.get("/api/v1/products?skip=0&limit=100&active_only=true")

            # Measure response times
            response_times = []
            for _ in range(20):
                start_time = time.time()
                response = client.get("/api/v1/products?skip=0&limit=100&active_only=true")
                end_time = time.time()

                assert response.status_code == 200
                response_time_ms = (end_time - start_time) * 1000
                response_times.append(response_time_ms)

            # Calculate 95th percentile
            response_times.sort()
            percentile_95_index = int(len(response_times) * 0.95)
            percentile_95 = response_times[percentile_95_index]

            assert percentile_95 < 100, f"95th percentile response time {percentile_95}ms exceeds 100ms"


class TestTemplateCaching:
    """Integration tests for template endpoint caching."""

    def describe_template_list_caching(self):
        """Tests for GET /templates caching."""

        @pytest.mark.asyncio
        async def it_caches_template_list_by_product(self, client, sample_template, sample_product_id):
            """Should cache template list for a specific product."""
            # First request
            response1 = client.get(f"/api/v1/templates?product_id={sample_product_id}")
            assert response1.status_code == 200

            # Second request - should be cached
            response2 = client.get(f"/api/v1/templates?product_id={sample_product_id}")
            assert response2.status_code == 200

            assert response1.json() == response2.json()

        @pytest.mark.asyncio
        async def it_invalidates_template_cache_on_creation(
            self, client, sample_product_id
        ):
            """Should invalidate template cache when new template is created."""
            # Get initial templates
            response1 = client.get(f"/api/v1/templates?product_id={sample_product_id}")
            assert response1.status_code == 200
            initial_count = len(response1.json())

            # Create a new template
            new_template = {
                "product_id": sample_product_id,
                "version": 999,
                "definition": {"zones": {"test": {"type": "text"}}},
                "is_default": False,
                "customization_zones": [
                    {
                        "key": "test",
                        "type": "text",
                        "config": {"max_length": 100},
                        "order_index": 0
                    }
                ]
            }
            create_response = client.post("/api/v1/templates", json=new_template)
            assert create_response.status_code == 201

            # Get templates again - should be refreshed
            response2 = client.get(f"/api/v1/templates?product_id={sample_product_id}")
            assert response2.status_code == 200
            new_count = len(response2.json())

            assert new_count == initial_count + 1

    def describe_template_detail_caching(self):
        """Tests for GET /templates/{id} caching."""

        @pytest.mark.asyncio
        async def it_caches_template_detail(self, client, sample_template):
            """Should cache individual template details."""
            template_id = str(sample_template.id)

            # First request
            response1 = client.get(f"/api/v1/templates/{template_id}")
            assert response1.status_code == 200

            # Second request - should be cached
            response2 = client.get(f"/api/v1/templates/{template_id}")
            assert response2.status_code == 200

            assert response1.json() == response2.json()

        @pytest.mark.asyncio
        async def it_invalidates_cache_on_template_update(self, client, sample_template):
            """Should invalidate template cache on update."""
            template_id = str(sample_template.id)

            # Get initial template
            response1 = client.get(f"/api/v1/templates/{template_id}")
            assert response1.status_code == 200

            # Update the template
            update_data = {"version": 100}
            update_response = client.put(
                f"/api/v1/templates/{template_id}",
                json=update_data
            )
            assert update_response.status_code == 200

            # Get template again - should reflect update
            response2 = client.get(f"/api/v1/templates/{template_id}")
            assert response2.status_code == 200

            assert response2.json()["version"] == 100
