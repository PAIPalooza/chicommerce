"""
Tests for AINative authentication service.

This module tests all authentication functionality including user registration,
login, token management, and comprehensive error handling.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
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


    @pytest.mark.asyncio
    async def test_register_user_successfully(self):
        """Should register a new user and return user data."""
        mock_response = {"id": "user_123", "email": "test@example.com", "name": "Test User"}
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response_obj = Mock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            mock_client.post.return_value = mock_response_obj
            mock_client_class.return_value.__aenter__.return_value = mock_client
            auth_service = AINativeAuthService()
            result = await auth_service.register_user("test@example.com", "SecurePass123!", "Test User")
            assert result == mock_response


    @pytest.mark.asyncio
    async def test_login_successfully(self):
        """Should login user and return tokens."""
        mock_response = {"access_token": "token123", "refresh_token": "refresh123"}
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response_obj = Mock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            mock_client.post.return_value = mock_response_obj
            mock_client_class.return_value.__aenter__.return_value = mock_client
            auth_service = AINativeAuthService()
            result = await auth_service.login("test@example.com", "SecurePass123!")
            assert "access_token" in result


    @pytest.mark.asyncio
    async def test_verify_token_returns_true_for_valid_token(self):
        """Should return True for valid token."""
        mock_user = {"id": "user_123", "email": "test@example.com"}
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response_obj = Mock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_user
            mock_client.get.return_value = mock_response_obj
            mock_client_class.return_value.__aenter__.return_value = mock_client
            auth_service = AINativeAuthService()
            result = await auth_service.verify_token("valid_token")
            assert result is True
