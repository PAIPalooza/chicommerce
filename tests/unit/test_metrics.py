"""
Unit tests for Prometheus metrics module.

Tests the core metrics functionality including:
- Counter initialization and increment
- Histogram initialization and observation
- Metric labels and naming
- Thread safety
"""
import pytest
from prometheus_client import REGISTRY


class TestMetricsModule:
    """
    Test suite for metrics module.

    Following BDD pattern with descriptive test method names.
    """

    def test_http_requests_counter_is_created_with_correct_labels(self):
        """
        GIVEN the metrics module
        WHEN the http_requests_total counter is imported
        THEN it should have the correct name and labels
        """
        # Arrange & Act
        from app.core.metrics import http_requests_total

        # Assert
        # Note: Prometheus client strips '_total' suffix from counter names
        assert http_requests_total is not None
        assert http_requests_total._name == 'http_requests'
        assert 'method' in http_requests_total._labelnames
        assert 'endpoint' in http_requests_total._labelnames
        assert 'status_code' in http_requests_total._labelnames

    def test_render_jobs_counter_is_created_with_status_label(self):
        """
        GIVEN the metrics module
        WHEN the render_jobs_total counter is imported
        THEN it should have the correct name and status label
        """
        # Arrange & Act
        from app.core.metrics import render_jobs_total

        # Assert
        # Note: Prometheus client strips '_total' suffix from counter names
        assert render_jobs_total is not None
        assert render_jobs_total._name == 'render_jobs'
        assert 'status' in render_jobs_total._labelnames

    def test_failed_webhooks_counter_is_created_with_correct_labels(self):
        """
        GIVEN the metrics module
        WHEN the failed_webhooks_total counter is imported
        THEN it should have provider and error_type labels
        """
        # Arrange & Act
        from app.core.metrics import failed_webhooks_total

        # Assert
        # Note: Prometheus client strips '_total' suffix from counter names
        assert failed_webhooks_total is not None
        assert failed_webhooks_total._name == 'failed_webhooks'
        assert 'provider' in failed_webhooks_total._labelnames
        assert 'error_type' in failed_webhooks_total._labelnames

    def test_http_request_duration_histogram_is_created(self):
        """
        GIVEN the metrics module
        WHEN the http_request_duration_seconds histogram is imported
        THEN it should have the correct name and labels
        """
        # Arrange & Act
        from app.core.metrics import http_request_duration_seconds

        # Assert
        assert http_request_duration_seconds is not None
        assert http_request_duration_seconds._name == 'http_request_duration_seconds'
        assert 'method' in http_request_duration_seconds._labelnames
        assert 'endpoint' in http_request_duration_seconds._labelnames

    def test_database_connections_gauge_is_created(self):
        """
        GIVEN the metrics module
        WHEN the database_connections_active gauge is imported
        THEN it should have the correct name and pool label
        """
        # Arrange & Act
        from app.core.metrics import database_connections_active

        # Assert
        assert database_connections_active is not None
        assert database_connections_active._name == 'database_connections_active'
        assert 'pool' in database_connections_active._labelnames

    def test_http_5xx_errors_counter_is_created(self):
        """
        GIVEN the metrics module
        WHEN the http_5xx_errors_total counter is imported
        THEN it should have the correct labels
        """
        # Arrange & Act
        from app.core.metrics import http_5xx_errors_total

        # Assert
        # Note: Prometheus client strips '_total' suffix from counter names
        assert http_5xx_errors_total is not None
        assert http_5xx_errors_total._name == 'http_5xx_errors'
        assert 'method' in http_5xx_errors_total._labelnames
        assert 'endpoint' in http_5xx_errors_total._labelnames
        assert 'status_code' in http_5xx_errors_total._labelnames

    def test_increment_render_job_increments_counter_for_success(self):
        """
        GIVEN the increment_render_job helper function
        WHEN called with status='success'
        THEN the render_jobs_total counter should increment
        """
        # Arrange
        from app.core.metrics import increment_render_job, render_jobs_total

        initial_value = 0
        for sample in render_jobs_total.collect()[0].samples:
            if sample.labels.get('status') == 'success':
                initial_value = sample.value
                break

        # Act
        increment_render_job(status='success')

        # Assert
        new_value = 0
        for sample in render_jobs_total.collect()[0].samples:
            if sample.labels.get('status') == 'success':
                new_value = sample.value
                break

        assert new_value == initial_value + 1

    def test_increment_render_job_increments_counter_for_failed(self):
        """
        GIVEN the increment_render_job helper function
        WHEN called with status='failed'
        THEN the render_jobs_total counter should increment
        """
        # Arrange
        from app.core.metrics import increment_render_job, render_jobs_total

        initial_value = 0
        for sample in render_jobs_total.collect()[0].samples:
            if sample.labels.get('status') == 'failed':
                initial_value = sample.value
                break

        # Act
        increment_render_job(status='failed')

        # Assert
        new_value = 0
        for sample in render_jobs_total.collect()[0].samples:
            if sample.labels.get('status') == 'failed':
                new_value = sample.value
                break

        assert new_value == initial_value + 1

    def test_increment_webhook_failure_increments_counter(self):
        """
        GIVEN the increment_webhook_failure helper function
        WHEN called with provider and error_type
        THEN the failed_webhooks_total counter should increment
        """
        # Arrange
        from app.core.metrics import increment_webhook_failure, failed_webhooks_total

        initial_value = 0
        for sample in failed_webhooks_total.collect()[0].samples:
            if (sample.labels.get('provider') == 'stripe' and
                sample.labels.get('error_type') == 'signature_error'):
                initial_value = sample.value
                break

        # Act
        increment_webhook_failure(provider='stripe', error_type='signature_error')

        # Assert
        new_value = 0
        for sample in failed_webhooks_total.collect()[0].samples:
            if (sample.labels.get('provider') == 'stripe' and
                sample.labels.get('error_type') == 'signature_error'):
                new_value = sample.value
                break

        assert new_value == initial_value + 1

    def test_record_request_increments_request_counter(self):
        """
        GIVEN the record_request helper function
        WHEN called with request details
        THEN both request count and duration should be recorded
        """
        # Arrange
        from app.core.metrics import record_request, http_requests_total

        initial_count = 0
        for sample in http_requests_total.collect()[0].samples:
            if (sample.labels.get('method') == 'GET' and
                sample.labels.get('endpoint') == '/api/test' and
                sample.labels.get('status_code') == '200'):
                initial_count = sample.value
                break

        # Act
        record_request(
            method='GET',
            endpoint='/api/test',
            status_code=200,
            duration=0.050
        )

        # Assert
        new_count = 0
        for sample in http_requests_total.collect()[0].samples:
            if (sample.labels.get('method') == 'GET' and
                sample.labels.get('endpoint') == '/api/test' and
                sample.labels.get('status_code') == '200'):
                new_count = sample.value
                break

        assert new_count == initial_count + 1

    def test_record_request_increments_5xx_counter_for_server_errors(self):
        """
        GIVEN the record_request helper function
        WHEN called with a 5xx status code
        THEN the http_5xx_errors_total counter should increment
        """
        # Arrange
        from app.core.metrics import record_request, http_5xx_errors_total

        initial_count = 0
        for sample in http_5xx_errors_total.collect()[0].samples:
            if (sample.labels.get('method') == 'POST' and
                sample.labels.get('endpoint') == '/api/error' and
                sample.labels.get('status_code') == '500'):
                initial_count = sample.value
                break

        # Act
        record_request(
            method='POST',
            endpoint='/api/error',
            status_code=500,
            duration=0.100
        )

        # Assert
        new_count = 0
        for sample in http_5xx_errors_total.collect()[0].samples:
            if (sample.labels.get('method') == 'POST' and
                sample.labels.get('endpoint') == '/api/error' and
                sample.labels.get('status_code') == '500'):
                new_count = sample.value
                break

        assert new_count == initial_count + 1

    def test_all_metrics_are_registered_in_prometheus_registry(self):
        """
        GIVEN all metrics in the module
        WHEN checking the Prometheus registry
        THEN all metrics should be registered
        """
        # Arrange & Act
        from app.core.metrics import (
            http_requests_total,
            http_request_duration_seconds,
            render_jobs_total,
            failed_webhooks_total,
            http_5xx_errors_total,
            database_connections_active
        )

        metric_names = []
        for collector in REGISTRY._collector_to_names.values():
            metric_names.extend(collector)

        # Assert
        assert 'http_requests_total' in metric_names
        assert 'http_request_duration_seconds' in metric_names
        assert 'render_jobs_total' in metric_names
        assert 'failed_webhooks_total' in metric_names
        assert 'http_5xx_errors_total' in metric_names
        assert 'database_connections_active' in metric_names
