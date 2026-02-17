"""
Unit tests for JWT Authentication Dependencies.

These tests verify the authentication logic without requiring database connectivity.
Following TDD principles and BDD patterns for GitHub Issue #6.

Security Requirements:
- JWT token validation works correctly
- Role-based access control enforces admin privileges
- API key fallback provides backward compatibility
- Proper error handling for invalid credentials
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt
from datetime import datetime, timedelta

from app.api import deps
from app.core.config import settings


def create_test_jwt(user_id: str = "test-user", role: str = "ADMIN",
                    email: str = "test@example.com", expired: bool = False) -> str:
    """
    Helper function to create a test JWT token.

    Args:
        user_id: User identifier
        role: User role (ADMIN or USER)
        email: User email
        expired: Whether to create an expired token

    Returns:
        Encoded JWT token string
    """
    payload = {
        "sub": user_id,
        "role": role,
        "email": email,
        "exp": datetime.utcnow() - timedelta(hours=1) if expired else datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


class TestVerifyJWTToken:
    """Test suite for JWT token verification logic."""

    @pytest.mark.asyncio
    async def test_valid_token_returns_payload(self):
        """
        GIVEN a valid JWT token
        WHEN verify_jwt_token is called
        THEN the decoded payload should be returned
        """
        # Arrange
        token = create_test_jwt(user_id="user123", role="ADMIN", email="admin@test.com")

        # Act
        result = await deps.verify_jwt_token(token)

        # Assert
        assert result["sub"] == "user123"
        assert result["role"] == "ADMIN"
        assert result["email"] == "admin@test.com"

    @pytest.mark.asyncio
    async def test_expired_token_raises_401(self):
        """
        GIVEN an expired JWT token
        WHEN verify_jwt_token is called
        THEN a 401 HTTPException should be raised
        """
        # Arrange
        expired_token = create_test_jwt(expired=True)

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await deps.verify_jwt_token(expired_token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid authentication credentials" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_invalid_signature_raises_401(self):
        """
        GIVEN a token with invalid signature
        WHEN verify_jwt_token is called
        THEN a 401 HTTPException should be raised
        """
        # Arrange
        payload = {
            "sub": "user123",
            "role": "ADMIN",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        invalid_token = jwt.encode(payload, "wrong-secret-key", algorithm="HS256")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await deps.verify_jwt_token(invalid_token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_malformed_token_raises_401(self):
        """
        GIVEN a malformed JWT token
        WHEN verify_jwt_token is called
        THEN a 401 HTTPException should be raised
        """
        # Arrange
        malformed_token = "not.a.valid.jwt.token"

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await deps.verify_jwt_token(malformed_token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_token_without_sub_raises_401(self):
        """
        GIVEN a token missing the 'sub' field
        WHEN verify_jwt_token is called
        THEN a 401 HTTPException should be raised with specific message
        """
        # Arrange
        payload = {
            "role": "ADMIN",
            "email": "test@example.com",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await deps.verify_jwt_token(token)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "missing user identifier" in exc_info.value.detail


class TestGetCurrentUser:
    """Test suite for get_current_user dependency."""

    @pytest.mark.asyncio
    async def test_valid_bearer_token_returns_user(self):
        """
        GIVEN valid bearer token credentials
        WHEN get_current_user is called
        THEN user information should be returned
        """
        # Arrange
        token = create_test_jwt(user_id="user123", role="USER")
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # Act
        result = await deps.get_current_user(credentials=credentials, api_key=None)

        # Assert
        assert result["sub"] == "user123"
        assert result["role"] == "USER"

    @pytest.mark.asyncio
    async def test_valid_api_key_returns_admin_user(self):
        """
        GIVEN valid API key
        WHEN get_current_user is called without bearer token
        THEN admin user information should be returned with deprecation notice
        """
        # Arrange
        valid_api_key = settings.ADMIN_API_KEY

        # Act
        result = await deps.get_current_user(credentials=None, api_key=valid_api_key)

        # Assert
        assert result["sub"] == "admin"
        assert result["role"] == "ADMIN"
        assert result["auth_method"] == "api_key_deprecated"

    @pytest.mark.asyncio
    async def test_invalid_api_key_raises_403(self):
        """
        GIVEN invalid API key
        WHEN get_current_user is called
        THEN a 403 HTTPException should be raised
        """
        # Arrange
        invalid_api_key = "wrong-api-key"

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await deps.get_current_user(credentials=None, api_key=invalid_api_key)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Invalid API Key" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_no_credentials_raises_401(self):
        """
        GIVEN no bearer token and no API key
        WHEN get_current_user is called
        THEN a 401 HTTPException should be raised
        """
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await deps.get_current_user(credentials=None, api_key=None)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Authentication required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_bearer_token_takes_precedence_over_api_key(self):
        """
        GIVEN both bearer token and API key
        WHEN get_current_user is called
        THEN bearer token should be used (takes precedence)
        """
        # Arrange
        token = create_test_jwt(user_id="jwt-user", role="USER")
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        api_key = settings.ADMIN_API_KEY

        # Act
        result = await deps.get_current_user(credentials=credentials, api_key=api_key)

        # Assert
        assert result["sub"] == "jwt-user"  # From JWT, not API key
        assert result["role"] == "USER"
        assert "auth_method" not in result  # JWT auth doesn't set this field


class TestGetAdminUser:
    """Test suite for get_admin_user dependency."""

    @pytest.mark.asyncio
    async def test_admin_role_passes(self):
        """
        GIVEN a user with ADMIN role
        WHEN get_admin_user is called
        THEN the user information should be returned
        """
        # Arrange
        admin_user = {
            "sub": "admin123",
            "role": "ADMIN",
            "email": "admin@test.com"
        }

        # Act
        result = await deps.get_admin_user(current_user=admin_user)

        # Assert
        assert result == admin_user

    @pytest.mark.asyncio
    async def test_user_role_raises_403(self):
        """
        GIVEN a user with USER role (not ADMIN)
        WHEN get_admin_user is called
        THEN a 403 HTTPException should be raised
        """
        # Arrange
        regular_user = {
            "sub": "user123",
            "role": "USER",
            "email": "user@test.com"
        }

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await deps.get_admin_user(current_user=regular_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Admin access required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_missing_role_raises_403(self):
        """
        GIVEN a user without a role field
        WHEN get_admin_user is called
        THEN a 403 HTTPException should be raised
        """
        # Arrange
        user_without_role = {
            "sub": "user123",
            "email": "user@test.com"
        }

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await deps.get_admin_user(current_user=user_without_role)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_role_check_is_case_insensitive(self):
        """
        GIVEN a user with lowercase 'admin' role
        WHEN get_admin_user is called
        THEN the check should pass (case-insensitive)
        """
        # Arrange
        admin_user = {
            "sub": "admin123",
            "role": "admin",  # lowercase
            "email": "admin@test.com"
        }

        # Act
        result = await deps.get_admin_user(current_user=admin_user)

        # Assert
        assert result == admin_user

    @pytest.mark.asyncio
    async def test_empty_role_raises_403(self):
        """
        GIVEN a user with empty role string
        WHEN get_admin_user is called
        THEN a 403 HTTPException should be raised
        """
        # Arrange
        user_with_empty_role = {
            "sub": "user123",
            "role": "",
            "email": "user@test.com"
        }

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await deps.get_admin_user(current_user=user_with_empty_role)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestGetOptionalUser:
    """Test suite for get_optional_user dependency."""

    @pytest.mark.asyncio
    async def test_valid_token_returns_user(self):
        """
        GIVEN valid bearer token credentials
        WHEN get_optional_user is called
        THEN user information should be returned
        """
        # Arrange
        token = create_test_jwt(user_id="user123", role="USER")
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # Act
        result = await deps.get_optional_user(credentials=credentials, api_key=None)

        # Assert
        assert result is not None
        assert result["sub"] == "user123"

    @pytest.mark.asyncio
    async def test_no_credentials_returns_none(self):
        """
        GIVEN no credentials
        WHEN get_optional_user is called
        THEN None should be returned (not an exception)
        """
        # Act
        result = await deps.get_optional_user(credentials=None, api_key=None)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_invalid_token_returns_none(self):
        """
        GIVEN invalid bearer token
        WHEN get_optional_user is called
        THEN None should be returned (not an exception)
        """
        # Arrange
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid.jwt.token"
        )

        # Act
        result = await deps.get_optional_user(credentials=credentials, api_key=None)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_valid_api_key_returns_user(self):
        """
        GIVEN valid API key
        WHEN get_optional_user is called
        THEN admin user information should be returned
        """
        # Arrange
        valid_api_key = settings.ADMIN_API_KEY

        # Act
        result = await deps.get_optional_user(credentials=None, api_key=valid_api_key)

        # Assert
        assert result is not None
        assert result["role"] == "ADMIN"


class TestDeprecatedGetAdminKey:
    """Test suite for deprecated get_admin_key function."""

    def test_valid_api_key_returns_key(self):
        """
        GIVEN a valid API key
        WHEN get_admin_key is called
        THEN the API key should be returned
        """
        # Arrange
        valid_key = settings.ADMIN_API_KEY

        # Act
        result = deps.get_admin_key(api_key=valid_key)

        # Assert
        assert result == valid_key

    def test_invalid_api_key_raises_403(self):
        """
        GIVEN an invalid API key
        WHEN get_admin_key is called
        THEN a 403 HTTPException should be raised
        """
        # Arrange
        invalid_key = "wrong-key"

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            deps.get_admin_key(api_key=invalid_key)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Invalid API Key" in exc_info.value.detail

    def test_missing_api_key_raises_401(self):
        """
        GIVEN no API key
        WHEN get_admin_key is called
        THEN a 401 HTTPException should be raised
        """
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            deps.get_admin_key(api_key=None)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "API key is required" in exc_info.value.detail
