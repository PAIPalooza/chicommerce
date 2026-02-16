"""
Security middleware for HTTPS redirection and security headers.

This module implements:
- HTTPS redirection for all HTTP requests
- Security headers (HSTS, CSP, X-Frame-Options, etc.)
- Following OWASP security best practices
"""
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """
    Middleware to redirect HTTP requests to HTTPS.

    This middleware checks the X-Forwarded-Proto header (set by reverse proxies)
    and redirects to HTTPS if the request came over HTTP.
    """

    def __init__(self, app: ASGIApp, enabled: bool = True):
        """
        Initialize the middleware.

        Args:
            app: The ASGI application
            enabled: Whether HTTPS redirection is enabled
        """
        super().__init__(app)
        self.enabled = enabled

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and redirect to HTTPS if necessary.

        Args:
            request: The incoming request
            call_next: The next middleware/handler in the chain

        Returns:
            Response: Either a redirect or the response from the next handler
        """
        if not self.enabled:
            return await call_next(request)

        # Check if request is using HTTP (via X-Forwarded-Proto header)
        forwarded_proto = request.headers.get("X-Forwarded-Proto", "")

        if forwarded_proto == "http":
            # Build HTTPS URL
            url = request.url.replace(scheme="https")

            # Return permanent redirect (308 to preserve method and body)
            return RedirectResponse(url=str(url), status_code=308)

        # Continue processing the request
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.

    Implements the following security headers:
    - Strict-Transport-Security (HSTS)
    - Content-Security-Policy (CSP)
    - X-Content-Type-Options
    - X-Frame-Options
    - X-XSS-Protection
    - Referrer-Policy
    - Permissions-Policy
    """

    def __init__(
        self,
        app: ASGIApp,
        enabled: bool = True,
        hsts_max_age: int = 31536000,
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = False
    ):
        """
        Initialize the middleware.

        Args:
            app: The ASGI application
            enabled: Whether security headers are enabled
            hsts_max_age: HSTS max-age in seconds
            hsts_include_subdomains: Include subdomains in HSTS
            hsts_preload: Enable HSTS preload
        """
        super().__init__(app)
        self.enabled = enabled
        self.hsts_max_age = hsts_max_age
        self.hsts_include_subdomains = hsts_include_subdomains
        self.hsts_preload = hsts_preload

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and add security headers to the response.

        Args:
            request: The incoming request
            call_next: The next middleware/handler in the chain

        Returns:
            Response: The response with added security headers
        """
        response = await call_next(request)

        if not self.enabled:
            return response

        # Build HSTS header value
        hsts_value = f"max-age={self.hsts_max_age}"
        if self.hsts_include_subdomains:
            hsts_value += "; includeSubDomains"
        if self.hsts_preload:
            hsts_value += "; preload"

        # Add security headers
        response.headers["Strict-Transport-Security"] = hsts_value

        # Content Security Policy - restrictive default policy
        # Adjust based on your application's needs
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Enable XSS protection (legacy but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy for privacy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy (Feature Policy replacement)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )

        return response
