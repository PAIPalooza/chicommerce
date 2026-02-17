"""
AINative authentication service.

This service handles authentication operations by proxying requests to the AINative API.
It provides user registration, login, token refresh, and user profile retrieval.
"""
from typing import Dict, Any
import httpx
from fastapi import HTTPException, status

from app.core.config import settings


class AINativeAuthService:
    """Service for AINative authentication."""

    def __init__(self):
        """Initialize AINative auth service."""
        self.base_url = f"{settings.AINATIVE_API_URL}v1/public/auth"
        self.api_token = settings.AINATIVE_API_TOKEN
        self.timeout = 30.0  # 30 second timeout for auth operations

    async def register_user(
        self,
        email: str,
        password: str,
        name: str
    ) -> Dict[str, Any]:
        """
        Register a new user.

        Args:
            email: User email address
            password: User password (min 8 characters)
            name: User full name

        Returns:
            User data including user_id, email, and name

        Raises:
            HTTPException: If registration fails (409 for duplicate email, 422 for validation errors)
        """
        url = f"{self.base_url}/register"
        payload = {
            "email": email,
            "password": password,
            "name": name
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 409:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already registered"
                )
            elif response.status_code == 422:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=response.json().get("detail", "Invalid registration data")
                )
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.json().get("detail", "Registration failed")
                )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service timeout"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Authentication service unavailable: {str(e)}"
            )

    async def login(self, email: str, password: str) -> Dict[str, str]:
        """
        Login user and get access token.

        Args:
            email: User email address
            password: User password

        Returns:
            Token response containing:
            - access_token: JWT access token
            - refresh_token: JWT refresh token
            - token_type: Bearer
            - expires_in: Token expiration time in seconds

        Raises:
            HTTPException: If login fails (401 for invalid credentials)
        """
        url = f"{self.base_url}/login-json"
        payload = {
            "email": email,
            "password": password
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication failed"
                )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service timeout"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Authentication service unavailable: {str(e)}"
            )

    async def get_current_user(self, access_token: str) -> Dict[str, Any]:
        """
        Get current user from access token.

        Args:
            access_token: JWT access token

        Returns:
            User data including user_id, email, name, and other profile information

        Raises:
            HTTPException: If token is invalid or expired (401)
        """
        url = f"{self.base_url}/me"
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication failed"
                )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service timeout"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Authentication service unavailable: {str(e)}"
            )

    async def refresh_token(self, refresh_token: str) -> Dict[str, str]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: JWT refresh token

        Returns:
            New token response containing:
            - access_token: New JWT access token
            - refresh_token: New JWT refresh token (optional, may be same as input)
            - token_type: Bearer
            - expires_in: Token expiration time in seconds

        Raises:
            HTTPException: If refresh token is invalid or expired (401)
        """
        url = f"{self.base_url}/refresh"
        headers = {"Authorization": f"Bearer {refresh_token}"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired refresh token"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token refresh failed"
                )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service timeout"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Authentication service unavailable: {str(e)}"
            )


# Factory function to get auth service instance
def get_auth_service() -> AINativeAuthService:
    """Get or create the auth service singleton instance."""
    if not hasattr(get_auth_service, '_instance'):
        get_auth_service._instance = AINativeAuthService()
    return get_auth_service._instance


# Legacy singleton instance for backward compatibility
auth_service = get_auth_service()
