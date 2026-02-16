"""
Prometheus metrics module.

This module provides Prometheus metrics for monitoring the application's
health, performance, and business KPIs including:
- HTTP request metrics (count, duration, errors)
- Render job metrics
- Webhook failure metrics
- Database connection pool metrics

All metrics follow Prometheus naming conventions:
- Counters: _total suffix
- Histograms: _seconds suffix for duration
- Gauges: current state
"""
from prometheus_client import Counter, Histogram, Gauge, REGISTRY


# HTTP Request Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total count of HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

http_5xx_errors_total = Counter(
    'http_5xx_errors_total',
    'Total count of HTTP 5xx errors',
    ['method', 'endpoint', 'status_code']
)

# Business Metrics
render_jobs_total = Counter(
    'render_jobs_total',
    'Total count of render jobs by status',
    ['status']
)

failed_webhooks_total = Counter(
    'failed_webhooks_total',
    'Total count of failed webhook deliveries',
    ['provider', 'error_type']
)

# System Metrics
database_connections_active = Gauge(
    'database_connections_active',
    'Number of active database connections',
    ['pool']
)


# Helper functions for common metric operations
def record_request(method: str, endpoint: str, status_code: int, duration: float) -> None:
    """
    Record HTTP request metrics.

    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: Request endpoint path
        status_code: HTTP status code
        duration: Request duration in seconds
    """
    status_str = str(status_code)

    # Record request count
    http_requests_total.labels(
        method=method,
        endpoint=endpoint,
        status_code=status_str
    ).inc()

    # Record request duration
    http_request_duration_seconds.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)

    # Record 5xx errors separately
    if 500 <= status_code < 600:
        http_5xx_errors_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_str
        ).inc()


def increment_render_job(status: str) -> None:
    """
    Increment render job counter.

    Args:
        status: Job status (success, failed, timeout, etc.)
    """
    render_jobs_total.labels(status=status).inc()


def increment_webhook_failure(provider: str, error_type: str) -> None:
    """
    Increment webhook failure counter.

    Args:
        provider: Payment provider (stripe, paypal, etc.)
        error_type: Type of error (signature_error, network_error, etc.)
    """
    failed_webhooks_total.labels(
        provider=provider,
        error_type=error_type
    ).inc()


def set_database_connections(pool_name: str, count: int) -> None:
    """
    Set current database connection count.

    Args:
        pool_name: Name of the connection pool
        count: Number of active connections
    """
    database_connections_active.labels(pool=pool_name).set(count)
