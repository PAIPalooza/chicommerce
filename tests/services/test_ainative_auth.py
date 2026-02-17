"""
Tests for AINative authentication service using TDD approach.

This module tests the AINative authentication service functionality including:
- User registration
- User login
- Token verification
- Get current user
- Token refresh
- Error handling for various failure scenarios
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from typing import Dict, Any

from fastapi import HTTPException, status
from app.services.ainative_auth import AINativeAuthService


class TestAINativeAuthService:
    """Test suite for AINativeAuthService class."""

    def test_initializes_with_default_settings(self):
        """Should initialize auth service with settings from config."""
        with patch('app.services.ainative_auth.settings') as mock_settings:
            mock_settings.AINATIVE_API_URL = "https://api.ainative.studio/"
            mock_settings.AINATIVE_API_TOKEN = "test_token"

            auth_service = AINativeAuthService()

            assert auth_service.base_url == "https://api.ainative.studio/v1/public/auth"
            assert auth_service.api_token == "test_token"


class TestUserRegistration:
    """Tests for user registration."""

    @pytest.mark.asyncio
    async def test_registers_user_successfully(self):
        """Should register a new user and return user data."""
        mock_response = {
            "id": "user_123",
            "email": "test@example.com",
            "name": "Test User",
            "role": "user",
            "created_at": "2026-02-17T10:00:00Z"
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response_obj = Mock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            mock_client.post.return_value = mock_response_obj
            mock_client_class.return_value.__aenter__.return_value = mock_client

            auth_service = AINativeAuthService()
            result = await auth_service.register_user(
                email="test@example.com",
                password="SecurePass123!",
                name="Test User"
            )

            assert result == mock_response
            assert result["email"] == "test@example.com"
            assert result["name"] == "Test User"

            # Verify API call
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0].endswith("/register")
            assert call_args[1]["json"]["email"] == "test@example.com"
            assert call_args[1]["json"]["password"] == "SecurePass123!"
            assert call_args[1]["json"]["name"] == "Test User"

    @pytest.mark.asyncio
    async def test_raises_exception_for_duplicate_email(self):
        """Should raise HTTPException when email already exists."""
        error_response = {
            "detail": "User with this email already exists"
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response_obj = Mock()
            mock_response_obj.status_code = 400
            mock_response_obj.json.return_value = error_response
            mock_client.post.return_value = mock_response_obj
            mock_client_class.return_value.__aenter__.return_value = mock_client

            auth_service = AINativeAuthService()

            with pytest.raises(HTTPException) as exc_info:
                await auth_service.register_user(
                    email="existing@example.com",
                    password="SecurePass123!",
                    name="Test User"
                )

            assert exc_info.value.status_code == 400
            assert "already exists" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_raises_exception_for_weak_password(self):
        """Should raise HTTPException for weak password."""
        error_response = {
            "detail": "Password does not meet security requirements"
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response_obj = Mock()
            mock_response_obj.status_code = 422
            mock_response_obj.json.return_value = error_response
            mock_client.post.return_value = mock_response_obj
            mock_client_class.return_value.__aenter__.return_value = mock_client

            auth_service = AINativeAuthService()

            with pytest.raises(HTTPException) as exc_info:
                await auth_service.register_user(
                    email="test@example.com",
                    password="weak",
                    name="Test User"
                )

            assert exc_info.value.status_code == 422

    @pytest.mark.asyncio
    async def test_handles_server_errors_gracefully(self):
        """Should handle server errors during registration."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response_obj = Mock()
            mock_response_obj.status_code = 500
            mock_response_obj.json.return_value = {"detail": "Internal server error"}
            mock_client.post.return_value = mock_response_obj
            mock_client_class.return_value.__aenter__.return_value = mock_client

            auth_service = AINativeAuthService()

            with pytest.raises(HTTPException) as exc_info:
                await auth_service.register_user(
                    email="test@example.com",
                    password="SecurePass123!",
                    name="Test User"
                )

            assert exc_info.value.status_code == 500


class TestUserLogin:
    """Tests for user login."""

    @pytest.mark.asyncio
    async def test_logs_in_user_successfully(self):
        """Should login user and return access and refresh tokens."""
        mock_response = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "expires_in": 3600
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response_obj = Mock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            mock_client.post.return_value = mock_response_obj
            mock_client_class.return_value.__aenter__.return_value = mock_client

            auth_service = AINativeAuthService()
            result = await auth_service.login(
                email="test@example.com",
                password="SecurePass123!"
            )

            assert "access_token" in result
            assert "refresh_token" in result
            assert result["token_type"] == "bearer"

            # Verify API call
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0].endswith("/login-json")
            assert call_args[1]["json"]["email"] == "test@example.com"
            assert call_args[1]["json"]["password"] == "SecurePass123!"

    @pytest.mark.asyncio
    async def test_raises_401_for_invalid_credentials(self):
        """Should raise HTTPException with 401 for invalid credentials."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response_obj = Mock()
            mock_response_obj.status_code = 401
            mock_response_obj.json.return_value = {"detail": "Invalid credentials"}
            mock_client.post.return_value = mock_response_obj
            mock_client_class.return_value.__aenter__.return_value = mock_client

            auth_service = AINativeAuthService()

            with pytest.raises(HTTPException) as exc_info:
                await auth_service.login(
                    email="test@example.com",
                    password="WrongPassword"
                )

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid credentials" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_raises_401_for_nonexistent_user(self):
        """Should raise HTTPException for non-existent user."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response_obj = Mock()
            mock_response_obj.status_code = 404
            mock_response_obj.json.return_value = {"detail": "User not found"}
            mock_client.post.return_value = mock_response_obj
            mock_client_class.return_value.__aenter__.return_value = mock_client

            auth_service = AINativeAuthService()

            with pytest.raises(HTTPException) as exc_info:
                await auth_service.login(
                    email="nonexistent@example.com",
                    password="SecurePass123!"
                )

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetCurrentUser:
    """Tests for getting current user from token."""

    @pytest.mark.asyncio
    async def test_gets_current_user_successfully(self):
        """Should get current user data from valid access token."""
        mock_user = {
            "id": "user_123",
            "email": "test@example.com",
            "name": "Test User",
            "role": "user",
            "is_active": True
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response_obj = Mock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_user
            mock_client.get.return_value = mock_response_obj
            mock_client_class.return_value.__aenter__.return_value = mock_client

            auth_service = AINativeAuthService()
            result = await auth_service.get_current_user(
                access_token="valid_token_here"
            )

            assert result == mock_user
            assert result["email"] == "test@example.com"

            # Verify API call with authorization header
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert call_args[0][0].endswith("/me")
            assert call_args[1]["headers"]["Authorization"] == "Bearer valid_token_here"

    @pytest.mark.asyncio
    async def test_raises_401_for_invalid_token(self):
        """Should raise HTTPException for invalid or expired token."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response_obj = Mock()
            mock_response_obj.status_code = 401
            mock_response_obj.json.return_value = {"detail": "Invalid token"}
            mock_client.get.return_value = mock_response_obj
            mock_client_class.return_value.__aenter__.return_value = mock_client

            auth_service = AINativeAuthService()

            with pytest.raises(HTTPException) as exc_info:
                await auth_service.get_current_user(access_token="invalid_token")

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid or expired token" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_raises_401_for_expired_token(self):
        """Should raise HTTPException for expired token."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response_obj = Mock()
            mock_response_obj.status_code = 401
            mock_response_obj.json.return_value = {"detail": "Token expired"}
            mock_client.get.return_value = mock_response_obj
            mock_client_class.return_value.__aenter__.return_value = mock_client

            auth_service = AINativeAuthService()

            with pytest.raises(HTTPException) as exc_info:
                await auth_service.get_current_user(access_token="expired_token")

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestRefreshToken:
    """Tests for token refresh."""

    @pytest.mark.asyncio
    async def test_refreshes_token_successfully(self):
        """Should refresh access token using valid refresh token."""
        mock_response = {
            "access_token": "new_access_token_here",
            "refresh_token": "new_refresh_token_here",
            "token_type": "bearer",
            "expires_in": 3600
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response_obj = Mock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            mock_client.post.return_value = mock_response_obj
            mock_client_class.return_value.__aenter__.return_value = mock_client

            auth_service = AINativeAuthService()
            result = await auth_service.refresh_token(
                refresh_token="valid_refresh_token"
            )

            assert "access_token" in result
            assert result["access_token"] == "new_access_token_here"

            # Verify API call
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0].endswith("/refresh")
            assert call_args[1]["headers"]["Authorization"] == "Bearer valid_refresh_token"

    @pytest.mark.asyncio
    async def test_raises_401_for_invalid_refresh_token(self):
        """Should raise HTTPException for invalid refresh token."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response_obj = Mock()
            mock_response_obj.status_code = 401
            mock_response_obj.json.return_value = {"detail": "Invalid refresh token"}
            mock_client.post.return_value = mock_response_obj
            mock_client_class.return_value.__aenter__.return_value = mock_client

            auth_service = AINativeAuthService()

            with pytest.raises(HTTPException) as exc_info:
                await auth_service.refresh_token(refresh_token="invalid_refresh_token")

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid refresh token" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_raises_401_for_expired_refresh_token(self):
        """Should raise HTTPException for expired refresh token."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response_obj = Mock()
            mock_response_obj.status_code = 401
            mock_response_obj.json.return_value = {"detail": "Refresh token expired"}
            mock_client.post.return_value = mock_response_obj
            mock_client_class.return_value.__aenter__.return_value = mock_client

            auth_service = AINativeAuthService()

            with pytest.raises(HTTPException) as exc_info:
                await auth_service.refresh_token(refresh_token="expired_refresh_token")

            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestVerifyToken:
    """Tests for token verification."""

    @pytest.mark.asyncio
    async def test_verifies_valid_token(self):
        """Should verify token and return True for valid token."""
        mock_user = {
            "id": "user_123",
            "email": "test@example.com",
            "name": "Test User"
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response_obj = Mock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_user
            mock_client.get.return_value = mock_response_obj
            mock_client_class.return_value.__aenter__.return_value = mock_client

            auth_service = AINativeAuthService()
            result = await auth_service.verify_token(token="valid_token")

            assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_for_invalid_token(self):
        """Should return False for invalid token without raising exception."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response_obj = Mock()
            mock_response_obj.status_code = 401
            mock_response_obj.json.return_value = {"detail": "Invalid token"}
            mock_client.get.return_value = mock_response_obj
            mock_client_class.return_value.__aenter__.return_value = mock_client

            auth_service = AINativeAuthService()
            result = await auth_service.verify_token(token="invalid_token")

            assert result is False

    @pytest.mark.asyncio
    async def test_handles_network_errors_gracefully(self):
        """Should handle network errors and return False."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = Exception("Network error")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            auth_service = AINativeAuthService()
            result = await auth_service.verify_token(token="any_token")

            assert result is False


class TestErrorHandling:
    """Tests for comprehensive error handling."""

    @pytest.mark.asyncio
    async def test_handles_timeout_errors(self):
        """Should handle timeout errors appropriately."""
        import httpx

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.TimeoutException("Request timeout")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            auth_service = AINativeAuthService()

            with pytest.raises(HTTPException) as exc_info:
                await auth_service.login(
                    email="test@example.com",
                    password="SecurePass123!"
                )

            assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            assert "timeout" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_handles_connection_errors(self):
        """Should handle connection errors appropriately."""
        import httpx

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.ConnectError("Connection failed")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            auth_service = AINativeAuthService()

            with pytest.raises(HTTPException) as exc_info:
                await auth_service.login(
                    email="test@example.com",
                    password="SecurePass123!"
                )

            assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            assert "unavailable" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_provides_meaningful_error_messages(self):
        """Should provide meaningful error messages from API responses."""
        error_response = {
            "detail": "Email format is invalid"
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response_obj = Mock()
            mock_response_obj.status_code = 422
            mock_response_obj.json.return_value = error_response
            mock_client.post.return_value = mock_response_obj
            mock_client_class.return_value.__aenter__.return_value = mock_client

            auth_service = AINativeAuthService()

            with pytest.raises(HTTPException) as exc_info:
                await auth_service.register_user(
                    email="invalid-email",
                    password="SecurePass123!",
                    name="Test User"
                )

            assert "Email format is invalid" in exc_info.value.detail
