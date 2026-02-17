"""
Integration tests for Authentication API endpoints.

This test suite provides comprehensive coverage of all authentication endpoints:
- POST /auth/register
- POST /auth/login
- POST /auth/refresh
- GET /auth/me
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import status
from fastapi.testclient import TestClient
import httpx

from app.main import app


@pytest.fixture
def auth_client():
    """
    Create a test client for auth endpoints that doesn't require database.

    Auth endpoints only call external services, so we don't need DB.
    """
    return TestClient(app)


class TestAuthenticationRegisterEndpoint:
    """
    Test suite for POST /auth/register endpoint.

    Following BDD pattern with descriptive test method names.
    """

    @patch('app.services.auth_service.httpx.AsyncClient')
    def test_register_user_successfully_creates_new_user(self, mock_async_client, auth_client):
        """
        GIVEN valid user registration data
        WHEN POST /auth/register is called
        THEN a new user should be created and returned with 201 status
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "user_id": "usr_123",
            "email": "newuser@example.com",
            "name": "New User",
            "is_active": True,
            "created_at": "2024-01-01T00:00:00Z"
        }

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        registration_data = {
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "name": "New User"
        }

        # Act
        response = auth_client.post("/api/v1/auth/register", json=registration_data)

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["user_id"] == "usr_123"
        assert data["email"] == "newuser@example.com"
        assert data["name"] == "New User"
        assert data["is_active"] is True

    @patch('app.services.auth_service.httpx.AsyncClient')
    def test_register_user_fails_with_duplicate_email(self, mock_async_client, auth_client):
        """
        GIVEN user registration data with existing email
        WHEN POST /auth/register is called
        THEN a 409 Conflict error should be returned
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 409
        mock_response.json.return_value = {"detail": "Email already registered"}

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        registration_data = {
            "email": "existing@example.com",
            "password": "SecurePass123!",
            "name": "Duplicate User"
        }

        # Act
        response = auth_client.post("/api/v1/auth/register", json=registration_data)

        # Assert
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "Email already registered" in response.json()["detail"]

    def test_register_user_fails_with_weak_password(self, auth_client):
        """
        GIVEN user registration data with weak password
        WHEN POST /auth/register is called
        THEN a 422 Validation error should be returned
        """
        # Arrange
        registration_data = {
            "email": "test@example.com",
            "password": "weak",  # Too short, no uppercase, no digit
            "name": "Test User"
        }

        # Act
        response = auth_client.post("/api/v1/auth/register", json=registration_data)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "detail" in response.json()

    def test_register_user_fails_with_invalid_email(self, auth_client):
        """
        GIVEN user registration data with invalid email
        WHEN POST /auth/register is called
        THEN a 422 Validation error should be returned
        """
        # Arrange
        registration_data = {
            "email": "not-an-email",
            "password": "SecurePass123!",
            "name": "Test User"
        }

        # Act
        response = auth_client.post("/api/v1/auth/register", json=registration_data)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "detail" in response.json()

    def test_register_user_fails_with_empty_name(self, auth_client):
        """
        GIVEN user registration data with empty name
        WHEN POST /auth/register is called
        THEN a 422 Validation error should be returned
        """
        # Arrange
        registration_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "name": "   "  # Empty/whitespace only
        }

        # Act
        response = auth_client.post("/api/v1/auth/register", json=registration_data)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_user_fails_with_missing_fields(self, auth_client):
        """
        GIVEN incomplete user registration data
        WHEN POST /auth/register is called
        THEN a 422 Validation error should be returned
        """
        # Arrange
        registration_data = {
            "email": "test@example.com"
            # Missing password and name
        }

        # Act
        response = auth_client.post("/api/v1/auth/register", json=registration_data)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch('app.services.auth_service.httpx.AsyncClient')
    def test_register_user_handles_service_timeout(self, mock_async_client, auth_client):
        """
        GIVEN valid registration data
        WHEN the authentication service times out
        THEN a 503 Service Unavailable error should be returned
        """
        # Arrange
        mock_client_instance = AsyncMock()
        mock_client_instance.post.side_effect = httpx.TimeoutException("Request timeout")
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        registration_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "name": "Test User"
        }

        # Act
        response = auth_client.post("/api/v1/auth/register", json=registration_data)

        # Assert
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "timeout" in response.json()["detail"].lower()


class TestAuthenticationLoginEndpoint:
    """
    Test suite for POST /auth/login endpoint.
    """

    @patch('app.services.auth_service.httpx.AsyncClient')
    def test_login_user_successfully_returns_tokens(self, mock_async_client, auth_client):
        """
        GIVEN valid user credentials
        WHEN POST /auth/login is called
        THEN access and refresh tokens should be returned
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh",
            "token_type": "bearer",
            "expires_in": 3600
        }

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        login_data = {
            "email": "user@example.com",
            "password": "SecurePass123!"
        }

        # Act
        response = auth_client.post("/api/v1/auth/login", json=login_data)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 3600

    @patch('app.services.auth_service.httpx.AsyncClient')
    def test_login_user_fails_with_invalid_credentials(self, mock_async_client, auth_client):
        """
        GIVEN invalid user credentials
        WHEN POST /auth/login is called
        THEN a 401 Unauthorized error should be returned
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"detail": "Invalid credentials"}

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        login_data = {
            "email": "user@example.com",
            "password": "WrongPassword123!"
        }

        # Act
        response = auth_client.post("/api/v1/auth/login", json=login_data)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    def test_login_user_fails_with_missing_email(self, auth_client):
        """
        GIVEN login data without email
        WHEN POST /auth/login is called
        THEN a 422 Validation error should be returned
        """
        # Arrange
        login_data = {
            "password": "SecurePass123!"
        }

        # Act
        response = auth_client.post("/api/v1/auth/login", json=login_data)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_user_fails_with_missing_password(self, auth_client):
        """
        GIVEN login data without password
        WHEN POST /auth/login is called
        THEN a 422 Validation error should be returned
        """
        # Arrange
        login_data = {
            "email": "user@example.com"
        }

        # Act
        response = auth_client.post("/api/v1/auth/login", json=login_data)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_user_fails_with_invalid_email_format(self, auth_client):
        """
        GIVEN login data with invalid email format
        WHEN POST /auth/login is called
        THEN a 422 Validation error should be returned
        """
        # Arrange
        login_data = {
            "email": "not-an-email",
            "password": "SecurePass123!"
        }

        # Act
        response = auth_client.post("/api/v1/auth/login", json=login_data)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch('app.services.auth_service.httpx.AsyncClient')
    def test_login_user_handles_service_timeout(self, mock_async_client, auth_client):
        """
        GIVEN valid login credentials
        WHEN the authentication service times out
        THEN a 503 Service Unavailable error should be returned
        """
        # Arrange
        mock_client_instance = AsyncMock()
        mock_client_instance.post.side_effect = httpx.TimeoutException("Request timeout")
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        login_data = {
            "email": "user@example.com",
            "password": "SecurePass123!"
        }

        # Act
        response = auth_client.post("/api/v1/auth/login", json=login_data)

        # Assert
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "timeout" in response.json()["detail"].lower()


class TestAuthenticationRefreshEndpoint:
    """
    Test suite for POST /auth/refresh endpoint.
    """

    @patch('app.services.auth_service.httpx.AsyncClient')
    def test_refresh_token_successfully_returns_new_tokens(self, mock_async_client, auth_client):
        """
        GIVEN valid refresh token
        WHEN POST /auth/refresh is called
        THEN new access token should be returned
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.new_access",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.new_refresh",
            "token_type": "bearer",
            "expires_in": 3600
        }

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        refresh_data = {
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.old_refresh"
        }

        # Act
        response = auth_client.post("/api/v1/auth/refresh", json=refresh_data)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @patch('app.services.auth_service.httpx.AsyncClient')
    def test_refresh_token_fails_with_invalid_token(self, mock_async_client, auth_client):
        """
        GIVEN invalid or expired refresh token
        WHEN POST /auth/refresh is called
        THEN a 401 Unauthorized error should be returned
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"detail": "Invalid refresh token"}

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        refresh_data = {
            "refresh_token": "invalid.refresh.token"
        }

        # Act
        response = auth_client.post("/api/v1/auth/refresh", json=refresh_data)

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    def test_refresh_token_fails_with_missing_token(self, auth_client):
        """
        GIVEN request without refresh token
        WHEN POST /auth/refresh is called
        THEN a 422 Validation error should be returned
        """
        # Arrange
        refresh_data = {}

        # Act
        response = auth_client.post("/api/v1/auth/refresh", json=refresh_data)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch('app.services.auth_service.httpx.AsyncClient')
    def test_refresh_token_handles_service_timeout(self, mock_async_client, auth_client):
        """
        GIVEN valid refresh token
        WHEN the authentication service times out
        THEN a 503 Service Unavailable error should be returned
        """
        # Arrange
        mock_client_instance = AsyncMock()
        mock_client_instance.post.side_effect = httpx.TimeoutException("Request timeout")
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        refresh_data = {
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh"
        }

        # Act
        response = auth_client.post("/api/v1/auth/refresh", json=refresh_data)

        # Assert
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "timeout" in response.json()["detail"].lower()


class TestAuthenticationGetCurrentUserEndpoint:
    """
    Test suite for GET /auth/me endpoint.
    """

    @patch('app.services.auth_service.httpx.AsyncClient')
    def test_get_current_user_successfully_returns_user_data(self, mock_async_client, auth_client):
        """
        GIVEN valid access token
        WHEN GET /auth/me is called
        THEN current user data should be returned
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "user_id": "usr_123",
            "email": "user@example.com",
            "name": "Test User",
            "is_active": True,
            "created_at": "2024-01-01T00:00:00Z"
        }

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        # Act
        response = auth_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_id"] == "usr_123"
        assert data["email"] == "user@example.com"
        assert data["name"] == "Test User"
        assert data["is_active"] is True

    @patch('app.services.auth_service.httpx.AsyncClient')
    def test_get_current_user_fails_with_invalid_token(self, mock_async_client, auth_client):
        """
        GIVEN invalid or expired access token
        WHEN GET /auth/me is called
        THEN a 401 Unauthorized error should be returned
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"detail": "Invalid token"}

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        # Act
        response = auth_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token"}
        )

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    def test_get_current_user_fails_without_authorization_header(self, auth_client):
        """
        GIVEN request without Authorization header
        WHEN GET /auth/me is called
        THEN a 422 Validation error should be returned
        """
        # Act
        response = auth_client.get("/api/v1/auth/me")

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_current_user_fails_with_malformed_authorization_header(self, auth_client):
        """
        GIVEN malformed Authorization header
        WHEN GET /auth/me is called
        THEN a 401 Unauthorized error should be returned
        """
        # Act
        response = auth_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "InvalidFormat token123"}
        )

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid authorization header format" in response.json()["detail"]

    def test_get_current_user_fails_with_empty_token(self, auth_client):
        """
        GIVEN Authorization header with empty token
        WHEN GET /auth/me is called
        THEN a 401 Unauthorized error should be returned
        """
        # Act
        response = auth_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer "}
        )

        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Access token is required" in response.json()["detail"]

    @patch('app.services.auth_service.httpx.AsyncClient')
    def test_get_current_user_handles_service_timeout(self, mock_async_client, auth_client):
        """
        GIVEN valid access token
        WHEN the authentication service times out
        THEN a 503 Service Unavailable error should be returned
        """
        # Arrange
        mock_client_instance = AsyncMock()
        mock_client_instance.get.side_effect = httpx.TimeoutException("Request timeout")
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        # Act
        response = auth_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access"}
        )

        # Assert
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "timeout" in response.json()["detail"].lower()


class TestAuthenticationEndpointIntegration:
    """
    Integration tests for authentication flow across multiple endpoints.
    """

    @patch('app.services.auth_service.httpx.AsyncClient')
    def test_complete_authentication_flow(self, mock_async_client, auth_client):
        """
        GIVEN a new user
        WHEN they register, login, refresh token, and access their profile
        THEN all operations should succeed with proper data flow
        """
        mock_client_instance = AsyncMock()

        # Mock register response
        register_response = MagicMock()
        register_response.status_code = 200
        register_response.json.return_value = {
            "user_id": "usr_123",
            "email": "integration@example.com",
            "name": "Integration User",
            "is_active": True
        }

        # Mock login response
        login_response = MagicMock()
        login_response.status_code = 200
        login_response.json.return_value = {
            "access_token": "access_token_123",
            "refresh_token": "refresh_token_123",
            "token_type": "bearer",
            "expires_in": 3600
        }

        # Mock refresh response
        refresh_response = MagicMock()
        refresh_response.status_code = 200
        refresh_response.json.return_value = {
            "access_token": "new_access_token_123",
            "refresh_token": "new_refresh_token_123",
            "token_type": "bearer",
            "expires_in": 3600
        }

        # Mock get user response
        user_response = MagicMock()
        user_response.status_code = 200
        user_response.json.return_value = {
            "user_id": "usr_123",
            "email": "integration@example.com",
            "name": "Integration User",
            "is_active": True
        }

        # Set up mock to return different responses based on call order
        mock_client_instance.post.side_effect = [register_response, login_response, refresh_response]
        mock_client_instance.get.return_value = user_response
        mock_async_client.return_value.__aenter__.return_value = mock_client_instance

        # Step 1: Register
        register_data = {
            "email": "integration@example.com",
            "password": "SecurePass123!",
            "name": "Integration User"
        }
        register_resp = client.post("/api/v1/auth/register", json=register_data)
        assert register_resp.status_code == status.HTTP_201_CREATED

        # Step 2: Login
        login_data = {
            "email": "integration@example.com",
            "password": "SecurePass123!"
        }
        login_resp = client.post("/api/v1/auth/login", json=login_data)
        assert login_resp.status_code == status.HTTP_200_OK
        tokens = login_resp.json()

        # Step 3: Get user profile
        user_resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert user_resp.status_code == status.HTTP_200_OK
        user_data = user_resp.json()
        assert user_data["email"] == "integration@example.com"

        # Step 4: Refresh token
        refresh_data = {
            "refresh_token": tokens["refresh_token"]
        }
        refresh_resp = client.post("/api/v1/auth/refresh", json=refresh_data)
        assert refresh_resp.status_code == status.HTTP_200_OK
        new_tokens = refresh_resp.json()
        assert "access_token" in new_tokens
