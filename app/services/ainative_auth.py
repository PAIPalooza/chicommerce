"""
AINative authentication service.

This service provides authentication functionality using the AINative API,
including user registration, login, token verification, and token refresh.

The service implements comprehensive error handling for network issues,
invalid credentials, and API failures.
"""
import httpx
from typing import Dict, Any
from fastapi import HTTPException, status

from app.core.config import settings


class AINativeAuthService:
    """
    Service for AINative authentication operations.

    This service handles all authentication-related operations with the
    AINative API, including:
    - User registration
    - User login
    - Token verification
    - Getting current user information
    - Refreshing access tokens

    All methods raise HTTPException for error cases to integrate seamlessly
    with FastAPI error handling.
    """

    def __init__(self):
        """
        Initialize AINative auth service.

        Sets up the base URL and API token from application settings.
        """
        self.base_url = f"{settings.AINATIVE_API_URL}v1/public/auth"
        self.api_token = settings.AINATIVE_API_TOKEN

    async def register_user(
        self,
        email: str,
        password: str,
        name: str
    ) -> Dict[str, Any]:
        """
        Register a new user with AINative.

        Args:
            email: User email address (must be unique)
            password: User password (must meet security requirements)
            name: User full name

        Returns:
            User data including id, email, name, role, and created_at

        Raises:
            HTTPException: If registration fails due to:
                - 400: Email already exists
                - 422: Invalid input (weak password, invalid email format)
                - 500: Server error
                - 503: Network/timeout errors
        """
        url = f"{self.base_url}/register"
        payload = {
            "email": email,
            "password": password,
            "name": name
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)

            if response.status_code == 200:
                return response.json()

            # Handle error responses
            error_detail = response.json().get("detail", "Registration failed")
            raise HTTPException(
                status_code=response.status_code,
                detail=error_detail
            )

        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Request timeout - AINative service unavailable"
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AINative service unavailable"
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error during registration: {str(e)}"
            )

    async def login(self, email: str, password: str) -> Dict[str, str]:
        """
        Login user and get access tokens.

        Args:
            email: User email address
            password: User password

        Returns:
            Token response containing:
                - access_token: JWT access token for API requests
                - refresh_token: JWT refresh token for obtaining new access tokens
                - token_type: Token type (usually "bearer")
                - expires_in: Token expiration time in seconds

        Raises:
            HTTPException: If login fails due to:
                - 401: Invalid credentials or user not found
                - 503: Network/timeout errors
        """
        url = f"{self.base_url}/login-json"
        payload = {
            "email": email,
            "password": password
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)

            if response.status_code == 200:
                return response.json()

            # All auth failures return 401
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Request timeout - AINative service unavailable"
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AINative service unavailable"
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error during login: {str(e)}"
            )

    async def get_current_user(self, access_token: str) -> Dict[str, Any]:
        """
        Get current user information from access token.

        Args:
            access_token: JWT access token

        Returns:
            User data including:
                - id: User ID
                - email: User email
                - name: User name
                - role: User role (e.g., "user", "admin")
                - is_active: Whether user account is active

        Raises:
            HTTPException: If token is invalid or expired (401)
        """
        url = f"{self.base_url}/me"
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)

            if response.status_code == 200:
                return response.json()

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )

        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Request timeout - AINative service unavailable"
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AINative service unavailable"
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error getting user: {str(e)}"
            )

    async def refresh_token(self, refresh_token: str) -> Dict[str, str]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: JWT refresh token

        Returns:
            New token response containing:
                - access_token: New JWT access token
                - refresh_token: New JWT refresh token
                - token_type: Token type (usually "bearer")
                - expires_in: Token expiration time in seconds

        Raises:
            HTTPException: If refresh token is invalid or expired (401)
        """
        url = f"{self.base_url}/refresh"
        headers = {"Authorization": f"Bearer {refresh_token}"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers)

            if response.status_code == 200:
                return response.json()

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Request timeout - AINative service unavailable"
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AINative service unavailable"
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error refreshing token: {str(e)}"
            )

    async def verify_token(self, token: str) -> bool:
        """
        Verify if a token is valid.

        This method attempts to get the current user with the token.
        Unlike other methods, it returns False instead of raising exceptions
        for invalid tokens, making it suitable for middleware and guards.

        Args:
            token: JWT access token to verify

        Returns:
            True if token is valid, False otherwise
        """
        try:
            await self.get_current_user(token)
            return True
        except Exception:
            # Any error means token is invalid
            return False
