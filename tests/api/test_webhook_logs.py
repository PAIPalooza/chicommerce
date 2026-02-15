"""
BDD-style tests for webhook logs audit endpoint.

This module tests the webhook logs auditing functionality including filtering,
pagination, and admin authentication.
"""
from datetime import datetime, timedelta
from typing import List
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.webhook_log import WebhookLog


@pytest.fixture
def sample_webhook_logs(db_session: Session) -> List[WebhookLog]:
    """Create sample webhook logs for testing."""
    logs = []

    # Create successful order.created webhook logs
    for i in range(15):
        log = WebhookLog(
            event_type="order.created",
            event_id=f"evt_order_{i}",
            url="https://example.com/webhooks/order",
            http_method="POST",
            payload='{"order_id": "123", "status": "created"}',
            headers='{"Content-Type": "application/json"}',
            response_status=200,
            response_body='{"success": true}',
            sent_at=datetime.utcnow() - timedelta(hours=i),
            response_time_ms=150 + i * 10,
            retry_count=0,
            is_success=True
        )
        logs.append(log)

    # Create failed order.created webhook logs
    for i in range(5):
        log = WebhookLog(
            event_type="order.created",
            event_id=f"evt_order_failed_{i}",
            url="https://example.com/webhooks/order",
            http_method="POST",
            payload='{"order_id": "456", "status": "created"}',
            headers='{"Content-Type": "application/json"}',
            response_status=500,
            response_body='{"error": "Internal server error"}',
            error_message="Server returned 500",
            sent_at=datetime.utcnow() - timedelta(hours=20 + i),
            response_time_ms=5000,
            retry_count=3,
            is_success=False
        )
        logs.append(log)

    # Create payment.succeeded webhook logs
    for i in range(10):
        log = WebhookLog(
            event_type="payment.succeeded",
            event_id=f"evt_payment_{i}",
            url="https://example.com/webhooks/payment",
            http_method="POST",
            payload='{"payment_id": "pi_123", "amount": 100}',
            headers='{"Content-Type": "application/json"}',
            response_status=200 if i % 3 != 0 else 404,
            response_body='{"success": true}' if i % 3 != 0 else '{"error": "Not found"}',
            error_message=None if i % 3 != 0 else "Endpoint not found",
            sent_at=datetime.utcnow() - timedelta(hours=30 + i),
            response_time_ms=200,
            retry_count=0 if i % 3 != 0 else 1,
            is_success=i % 3 != 0
        )
        logs.append(log)

    # Add all logs to database
    db_session.add_all(logs)
    db_session.commit()

    return logs


class TestWebhookLogsAuthentication:
    """Tests for admin authentication on webhook logs endpoint."""

    def test_require_authentication(self, client: TestClient):
        """Should require admin authentication to access webhook logs."""
        # Remove authentication
        client.set_auth(None)

        response = client.get("/api/v1/webhooklogs")

        assert response.status_code == 401
        assert "required" in response.json()["detail"].lower()

    def test_reject_invalid_api_key(self, client: TestClient):
        """Should reject requests with invalid API key."""
        # Temporarily remove auth override to test actual API key validation
        client.set_auth(None)

        response = client.get(
            "/api/v1/webhooklogs",
            headers={"X-API-Key": "invalid-key"}
        )

        assert response.status_code == 403
        assert "invalid" in response.json()["detail"].lower()

        # Restore auth for other tests
        client.set_auth("test-admin-key")

    def test_accept_valid_api_key(
        self, client: TestClient, sample_webhook_logs: List[WebhookLog]
    ):
        """Should accept requests with valid admin API key."""
        response = client.get(
            "/api/v1/webhooklogs",
            headers={"X-API-Key": "test-admin-key"}
        )

        assert response.status_code == 200
        assert "items" in response.json()


class TestWebhookLogsBasicRetrieval:
    """Tests for basic webhook logs retrieval."""

    def test_return_webhook_logs_with_required_fields(
        self, client: TestClient, sample_webhook_logs: List[WebhookLog]
    ):
        """Should return webhook logs with event_type, response_status, and sent_at."""
        response = client.get(
            "/api/v1/webhooklogs",
            headers={"X-API-Key": "test-admin-key"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert len(data["items"]) > 0

        # Verify required fields
        first_log = data["items"][0]
        assert "event_type" in first_log
        assert "response_status" in first_log
        assert "sent_at" in first_log
        assert "id" in first_log
        assert "url" in first_log
        assert "is_success" in first_log

    def test_return_logs_sorted_by_sent_at_desc(
        self, client: TestClient, sample_webhook_logs: List[WebhookLog]
    ):
        """Should return webhook logs sorted by sent_at in descending order (newest first)."""
        response = client.get(
            "/api/v1/webhooklogs",
            headers={"X-API-Key": "test-admin-key"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify logs are sorted by sent_at descending
        items = data["items"]
        if len(items) > 1:
            for i in range(len(items) - 1):
                current_time = datetime.fromisoformat(items[i]["sent_at"].replace('Z', '+00:00'))
                next_time = datetime.fromisoformat(items[i + 1]["sent_at"].replace('Z', '+00:00'))
                assert current_time >= next_time, "Logs should be sorted by sent_at descending"


class TestWebhookLogsFilteringByEvent:
    """Tests for filtering webhook logs by event type."""

    def test_filter_logs_by_event_type_using_event_param(
        self, client: TestClient, sample_webhook_logs: List[WebhookLog]
    ):
        """Should filter webhook logs by event type using 'event' query parameter."""
        response = client.get(
            "/api/v1/webhooklogs?event=order.created",
            headers={"X-API-Key": "test-admin-key"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        # Should have 20 order.created logs (15 success + 5 failed)
        assert data["total"] == 20

        # Verify all returned logs have the correct event type
        for log in data["items"]:
            assert log["event_type"] == "order.created"

    def test_filter_logs_by_payment_succeeded_event(
        self, client: TestClient, sample_webhook_logs: List[WebhookLog]
    ):
        """Should filter webhook logs for payment.succeeded events."""
        response = client.get(
            "/api/v1/webhooklogs?event=payment.succeeded",
            headers={"X-API-Key": "test-admin-key"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        # Should have 10 payment.succeeded logs
        assert data["total"] == 10

        # Verify all returned logs have the correct event type
        for log in data["items"]:
            assert log["event_type"] == "payment.succeeded"

    def test_return_all_logs_when_no_event_filter_provided(
        self, client: TestClient, sample_webhook_logs: List[WebhookLog]
    ):
        """Should return all webhook logs when no event filter is provided."""
        response = client.get(
            "/api/v1/webhooklogs",
            headers={"X-API-Key": "test-admin-key"}
        )

        assert response.status_code == 200
        data = response.json()

        # Should have all 30 logs (20 order.created + 10 payment.succeeded)
        assert data["total"] == 30


class TestWebhookLogsFilteringByStatus:
    """Tests for filtering webhook logs by HTTP response status."""

    def test_filter_logs_by_response_status_200(
        self, client: TestClient, sample_webhook_logs: List[WebhookLog]
    ):
        """Should filter webhook logs by HTTP response status 200."""
        response = client.get(
            "/api/v1/webhooklogs?status=200",
            headers={"X-API-Key": "test-admin-key"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify all returned logs have status 200
        for log in data["items"]:
            assert log["response_status"] == 200

    def test_filter_logs_by_response_status_500(
        self, client: TestClient, sample_webhook_logs: List[WebhookLog]
    ):
        """Should filter webhook logs by HTTP response status 500."""
        response = client.get(
            "/api/v1/webhooklogs?status=500",
            headers={"X-API-Key": "test-admin-key"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 5  # 5 failed order.created logs

        # Verify all returned logs have status 500
        for log in data["items"]:
            assert log["response_status"] == 500

    def test_filter_logs_by_success_status(
        self, client: TestClient, sample_webhook_logs: List[WebhookLog]
    ):
        """Should filter webhook logs by success status."""
        response = client.get(
            "/api/v1/webhooklogs?success=true",
            headers={"X-API-Key": "test-admin-key"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify all returned logs are successful
        for log in data["items"]:
            assert log["is_success"] is True

    def test_combine_event_and_status_filters(
        self, client: TestClient, sample_webhook_logs: List[WebhookLog]
    ):
        """Should support combining event type and status filters."""
        response = client.get(
            "/api/v1/webhooklogs?event=order.created&status=500",
            headers={"X-API-Key": "test-admin-key"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 5  # 5 failed order.created logs

        # Verify all returned logs match both filters
        for log in data["items"]:
            assert log["event_type"] == "order.created"
            assert log["response_status"] == 500


class TestWebhookLogsPagination:
    """Tests for pagination of webhook logs."""

    def test_support_limit_parameter(
        self, client: TestClient, sample_webhook_logs: List[WebhookLog]
    ):
        """Should support pagination with limit parameter."""
        response = client.get(
            "/api/v1/webhooklogs?limit=10",
            headers={"X-API-Key": "test-admin-key"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert len(data["items"]) == 10
        assert data["limit"] == 10
        assert data["total"] == 30
        assert data["has_more"] is True

    def test_support_offset_parameter(
        self, client: TestClient, sample_webhook_logs: List[WebhookLog]
    ):
        """Should support pagination with offset parameter."""
        response = client.get(
            "/api/v1/webhooklogs?limit=10&offset=10",
            headers={"X-API-Key": "test-admin-key"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert len(data["items"]) == 10
        assert data["offset"] == 10
        assert data["total"] == 30
        assert data["has_more"] is True

    def test_indicate_no_more_items_on_last_page(
        self, client: TestClient, sample_webhook_logs: List[WebhookLog]
    ):
        """Should indicate no more items when on the last page."""
        response = client.get(
            "/api/v1/webhooklogs?limit=50",
            headers={"X-API-Key": "test-admin-key"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["has_more"] is False
        assert data["total"] == 30
        assert len(data["items"]) == 30

    def test_enforce_maximum_limit_of_100(
        self, client: TestClient, sample_webhook_logs: List[WebhookLog]
    ):
        """Should enforce maximum limit of 100 items per page."""
        response = client.get(
            "/api/v1/webhooklogs?limit=200",
            headers={"X-API-Key": "test-admin-key"}
        )

        # Should reject with validation error
        assert response.status_code == 422

    def test_default_to_50_items_when_limit_not_specified(
        self, client: TestClient, sample_webhook_logs: List[WebhookLog]
    ):
        """Should default to 50 items per page when limit is not specified."""
        response = client.get(
            "/api/v1/webhooklogs",
            headers={"X-API-Key": "test-admin-key"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["limit"] == 50
        # We have 30 total logs, so should return all 30
        assert len(data["items"]) == 30

    def test_support_pagination_with_filters(
        self, client: TestClient, sample_webhook_logs: List[WebhookLog]
    ):
        """Should support pagination combined with filtering."""
        response = client.get(
            "/api/v1/webhooklogs?event=order.created&limit=5&offset=5",
            headers={"X-API-Key": "test-admin-key"}
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["items"]) == 5
        assert data["total"] == 20  # Total order.created logs
        assert data["offset"] == 5
        assert data["has_more"] is True

        # Verify all logs match the filter
        for log in data["items"]:
            assert log["event_type"] == "order.created"


class TestWebhookLogsResponseFormat:
    """Tests for webhook log response format."""

    def test_include_all_audit_fields(
        self, client: TestClient, sample_webhook_logs: List[WebhookLog]
    ):
        """Should include all relevant audit fields in the response."""
        response = client.get(
            "/api/v1/webhooklogs?limit=1",
            headers={"X-API-Key": "test-admin-key"}
        )

        assert response.status_code == 200
        data = response.json()

        log = data["items"][0]
        # Verify all expected fields are present
        expected_fields = [
            "id", "event_type", "event_id", "url", "http_method",
            "response_status", "sent_at", "response_time_ms",
            "retry_count", "is_success", "created_at"
        ]
        for field in expected_fields:
            assert field in log, f"Field '{field}' should be present in response"

    def test_include_error_messages_for_failed_deliveries(
        self, client: TestClient, sample_webhook_logs: List[WebhookLog]
    ):
        """Should include error messages for failed webhook deliveries."""
        response = client.get(
            "/api/v1/webhooklogs?success=false",
            headers={"X-API-Key": "test-admin-key"}
        )

        assert response.status_code == 200
        data = response.json()

        # Find a log with an error message
        log_with_error = None
        for log in data["items"]:
            if log.get("error_message"):
                log_with_error = log
                break

        assert log_with_error is not None
        assert log_with_error["error_message"] is not None
        assert log_with_error["is_success"] is False


class TestWebhookLogsEdgeCases:
    """Tests for edge cases in webhook logs endpoint."""

    def test_return_empty_list_when_no_logs_match_filter(
        self, client: TestClient, sample_webhook_logs: List[WebhookLog]
    ):
        """Should return empty list when no logs match the filter."""
        response = client.get(
            "/api/v1/webhooklogs?event=nonexistent.event",
            headers={"X-API-Key": "test-admin-key"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["items"] == []
        assert data["total"] == 0
        assert data["has_more"] is False

    def test_handle_offset_beyond_total_results(
        self, client: TestClient, sample_webhook_logs: List[WebhookLog]
    ):
        """Should handle offset beyond total results gracefully."""
        response = client.get(
            "/api/v1/webhooklogs?offset=1000",
            headers={"X-API-Key": "test-admin-key"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["items"] == []
        assert data["total"] == 30
        assert data["offset"] == 1000
        assert data["has_more"] is False
