"""
API tests for /metrics endpoint.

Tests Prometheus metrics exposure via HTTP endpoint.
"""
import pytest
from fastapi.testclient import TestClient


class TestMetricsEndpoint:
    """
    Test suite for the /metrics endpoint.

    Following BDD pattern with descriptive test method names.
    """

    def test_metrics_endpoint_returns_200(self, client: TestClient):
        """
        GIVEN the FastAPI application with metrics enabled
        WHEN GET /metrics is requested
        THEN it should return 200 OK
        """
        # Act
        response = client.get("/metrics")

        # Assert
        assert response.status_code == 200

    def test_metrics_endpoint_returns_prometheus_format(self, client: TestClient):
        """
        GIVEN the FastAPI application with metrics enabled
        WHEN GET /metrics is requested
        THEN it should return Prometheus text format
        """
        # Act
        response = client.get("/metrics")

        # Assert
        assert response.status_code == 200
        # Prometheus metrics use text/plain with version parameter
        assert "text/plain" in response.headers.get("content-type", "")

    def test_metrics_endpoint_contains_http_requests_total(self, client: TestClient):
        """
        GIVEN the FastAPI application with metrics enabled
        WHEN GET /metrics is requested
        THEN it should include http_requests_total metric
        """
        # Act
        response = client.get("/metrics")

        # Assert
        assert response.status_code == 200
        assert "http_requests_total" in response.text

    def test_metrics_endpoint_contains_render_jobs_total(self, client: TestClient):
        """
        GIVEN the FastAPI application with metrics enabled
        WHEN GET /metrics is requested
        THEN it should include render_jobs_total metric
        """
        # Act
        response = client.get("/metrics")

        # Assert
        assert response.status_code == 200
        assert "render_jobs_total" in response.text

    def test_metrics_endpoint_contains_failed_webhooks_total(self, client: TestClient):
        """
        GIVEN the FastAPI application with metrics enabled
        WHEN GET /metrics is requested
        THEN it should include failed_webhooks_total metric
        """
        # Act
        response = client.get("/metrics")

        # Assert
        assert response.status_code == 200
        assert "failed_webhooks_total" in response.text

    def test_metrics_endpoint_contains_http_5xx_errors_total(self, client: TestClient):
        """
        GIVEN the FastAPI application with metrics enabled
        WHEN GET /metrics is requested
        THEN it should include http_5xx_errors_total metric
        """
        # Act
        response = client.get("/metrics")

        # Assert
        assert response.status_code == 200
        assert "http_5xx_errors_total" in response.text

    def test_metrics_endpoint_contains_http_request_duration_seconds(self, client: TestClient):
        """
        GIVEN the FastAPI application with metrics enabled
        WHEN GET /metrics is requested
        THEN it should include http_request_duration_seconds histogram
        """
        # Act
        response = client.get("/metrics")

        # Assert
        assert response.status_code == 200
        assert "http_request_duration_seconds" in response.text

    def test_metrics_endpoint_records_own_request(self, client: TestClient):
        """
        GIVEN the FastAPI application with metrics middleware
        WHEN GET /metrics is requested multiple times
        THEN it should record metrics for the /metrics endpoint itself
        """
        # Act
        response1 = client.get("/metrics")
        response2 = client.get("/metrics")

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        # The metrics endpoint should track its own requests
        assert 'endpoint="/metrics"' in response2.text or 'endpoint="/metrics"' in response1.text


class TestMetricsMiddleware:
    """
    Test suite for metrics middleware that records HTTP requests.

    Following BDD pattern with descriptive test method names.
    """

    def test_middleware_records_successful_request(self, client: TestClient):
        """
        GIVEN the FastAPI application with metrics middleware
        WHEN a successful request is made
        THEN the metrics should record the request with status 200
        """
        # Act
        response = client.get("/health")
        metrics_response = client.get("/metrics")

        # Assert
        assert response.status_code == 200
        assert metrics_response.status_code == 200
        # Check that health endpoint request was recorded
        assert 'endpoint="/health"' in metrics_response.text
        assert 'status_code="200"' in metrics_response.text

    def test_middleware_records_404_error(self, client: TestClient):
        """
        GIVEN the FastAPI application with metrics middleware
        WHEN a request to non-existent endpoint is made
        THEN the metrics should record the request with status 404
        """
        # Act
        response = client.get("/nonexistent")
        metrics_response = client.get("/metrics")

        # Assert
        assert response.status_code == 404
        assert metrics_response.status_code == 200
        # Check that 404 was recorded
        assert 'status_code="404"' in metrics_response.text

    def test_middleware_includes_request_method_in_metrics(self, client: TestClient):
        """
        GIVEN the FastAPI application with metrics middleware
        WHEN requests with different methods are made
        THEN the metrics should include the HTTP method label
        """
        # Act - make a GET request
        get_response = client.get("/health")
        # Get metrics
        metrics_response = client.get("/metrics")

        # Assert
        assert get_response.status_code == 200
        assert 'method="GET"' in metrics_response.text

    def test_middleware_records_request_duration(self, client: TestClient):
        """
        GIVEN the FastAPI application with metrics middleware
        WHEN requests are made
        THEN the metrics should include request duration histogram
        """
        # Act
        response = client.get("/health")
        metrics_response = client.get("/metrics")

        # Assert
        assert response.status_code == 200
        # Check for histogram metrics (bucket, count, sum)
        assert "http_request_duration_seconds_bucket" in metrics_response.text
        assert "http_request_duration_seconds_count" in metrics_response.text
        assert "http_request_duration_seconds_sum" in metrics_response.text
