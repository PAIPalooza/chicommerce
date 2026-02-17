"""
Metrics middleware for FastAPI.

This middleware automatically records HTTP request metrics including:
- Request count by method, endpoint, and status code
- Request duration histogram
- HTTP 5xx error count
"""
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.metrics import record_request


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to record Prometheus metrics for all HTTP requests.

    Records:
    - http_requests_total: Counter of requests by method/endpoint/status
    - http_request_duration_seconds: Histogram of request durations
    - http_5xx_errors_total: Counter of 5xx errors

    The middleware captures the request start time, processes the request,
    and then records the metrics with the appropriate labels.
    """

    def __init__(self, app: ASGIApp):
        """
        Initialize the metrics middleware.

        Args:
            app: The ASGI application
        """
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and record metrics.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler

        Returns:
            The HTTP response
        """
        # Record start time
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Get endpoint path (use path template if available, otherwise raw path)
        endpoint = request.url.path

        # Record metrics
        record_request(
            method=request.method,
            endpoint=endpoint,
            status_code=response.status_code,
            duration=duration
        )

        return response
