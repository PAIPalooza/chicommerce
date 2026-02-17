"""
Integration tests for JWT Authentication Dependencies.

Following BDD (Behavior-Driven Development) patterns and TDD principles
to verify JWT authentication requirements per GitHub Issue #6.

Security Requirements:
- JWT Bearer tokens are supported for authentication
- Admin endpoints accept JWT tokens with ADMIN role
- API key authentication still works (backward compatibility)
- API key usage logs deprecation warnings
- Invalid tokens are properly rejected
- Role-based access control is enforced
"""
import pytest
from fastapi import status
from jose import jwt
from datetime import datetime, timedelta
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


class TestJWTAuthenticationBasics:
    """
    Test suite for basic JWT authentication functionality.

    Verifies that JWT tokens are properly validated and user info is extracted.
    """

    def test_create_product_with_valid_jwt_token(self, client, sample_product_data):
        """
        GIVEN a valid JWT token with ADMIN role
        WHEN the POST /api/v1/products/ endpoint is called with Authorization: Bearer header
        THEN the product should be created successfully (201)
        """
        # Arrange
        token = create_test_jwt(user_id="admin-user", role="ADMIN")

        # Act
        response = client.post(
            "/api/v1/products/",
            json=sample_product_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == sample_product_data["name"]
        assert "id" in data

    def test_create_product_with_missing_bearer_token(self, client, sample_product_data):
        """
        GIVEN no authentication headers
        WHEN the POST /api/v1/products/ endpoint is called
        THEN a 401 Unauthorized response should be returned
        """
        # Arrange - Remove authentication
        client.set_auth(None)

        try:
            # Act
            response = client.post(
                "/api/v1/products/",
                json=sample_product_data
            )

            # Assert
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Authentication required" in response.json()["detail"]
        finally:
            client.set_auth("test-admin-key")

    def test_create_product_with_invalid_jwt_token(self, client, sample_product_data):
        """
        GIVEN an invalid JWT token (wrong signature)
        WHEN the POST /api/v1/products/ endpoint is called
        THEN a 401 Unauthorized response should be returned
        """
        # Arrange
        client.set_auth(None)
        invalid_token = "invalid.jwt.token.signature.here"

        try:
            # Act
            response = client.post(
                "/api/v1/products/",
                json=sample_product_data,
                headers={"Authorization": f"Bearer {invalid_token}"}
            )

            # Assert
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid authentication credentials" in response.json()["detail"]
        finally:
            client.set_auth("test-admin-key")

    def test_create_product_with_expired_jwt_token(self, client, sample_product_data):
        """
        GIVEN an expired JWT token
        WHEN the POST /api/v1/products/ endpoint is called
        THEN a 401 Unauthorized response should be returned
        """
        # Arrange
        client.set_auth(None)
        expired_token = create_test_jwt(user_id="admin-user", role="ADMIN", expired=True)

        try:
            # Act
            response = client.post(
                "/api/v1/products/",
                json=sample_product_data,
                headers={"Authorization": f"Bearer {expired_token}"}
            )

            # Assert
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
        finally:
            client.set_auth("test-admin-key")

    def test_create_product_with_malformed_bearer_header(self, client, sample_product_data):
        """
        GIVEN a malformed Authorization header (missing 'Bearer' prefix)
        WHEN the POST /api/v1/products/ endpoint is called
        THEN a 401 Unauthorized response should be returned
        """
        # Arrange
        client.set_auth(None)
        token = create_test_jwt(user_id="admin-user", role="ADMIN")

        try:
            # Act - Missing 'Bearer' prefix
            response = client.post(
                "/api/v1/products/",
                json=sample_product_data,
                headers={"Authorization": token}
            )

            # Assert
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
        finally:
            client.set_auth("test-admin-key")


class TestRoleBasedAccessControl:
    """
    Test suite for role-based access control (RBAC).

    Verifies that admin endpoints properly check user roles.
    """

    def test_admin_endpoint_rejects_user_role(self, client, sample_product_data):
        """
        GIVEN a valid JWT token with USER role (not ADMIN)
        WHEN the POST /api/v1/products/ endpoint is called
        THEN a 403 Forbidden response should be returned
        """
        # Arrange
        client.set_auth(None)
        user_token = create_test_jwt(user_id="regular-user", role="USER")

        try:
            # Act
            response = client.post(
                "/api/v1/products/",
                json=sample_product_data,
                headers={"Authorization": f"Bearer {user_token}"}
            )

            # Assert
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert "Admin access required" in response.json()["detail"]
        finally:
            client.set_auth("test-admin-key")

    def test_admin_endpoint_accepts_admin_role(self, client, sample_product_data):
        """
        GIVEN a valid JWT token with ADMIN role
        WHEN the POST /api/v1/products/ endpoint is called
        THEN the request should succeed (201)
        """
        # Arrange
        admin_token = create_test_jwt(user_id="admin-user", role="ADMIN")

        # Act
        response = client.post(
            "/api/v1/products/",
            json=sample_product_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED

    def test_admin_endpoint_rejects_missing_role(self, client, sample_product_data):
        """
        GIVEN a JWT token without a role field
        WHEN the POST /api/v1/products/ endpoint is called
        THEN a 403 Forbidden response should be returned
        """
        # Arrange
        client.set_auth(None)
        payload = {
            "sub": "user-without-role",
            "email": "test@example.com",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        try:
            # Act
            response = client.post(
                "/api/v1/products/",
                json=sample_product_data,
                headers={"Authorization": f"Bearer {token}"}
            )

            # Assert
            assert response.status_code == status.HTTP_403_FORBIDDEN
        finally:
            client.set_auth("test-admin-key")

    def test_role_is_case_insensitive(self, client, sample_product_data):
        """
        GIVEN a JWT token with lowercase 'admin' role
        WHEN the POST /api/v1/products/ endpoint is called
        THEN the request should succeed (role checking is case-insensitive)
        """
        # Arrange
        admin_token = create_test_jwt(user_id="admin-user", role="admin")  # lowercase

        # Act
        response = client.post(
            "/api/v1/products/",
            json=sample_product_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED


class TestBackwardCompatibility:
    """
    Test suite for backward compatibility with API key authentication.

    Verifies that existing API key authentication still works during transition period.
    """

    def test_api_key_still_works_for_admin_endpoints(self, client, sample_product_data):
        """
        GIVEN a valid API key in X-API-Key header
        WHEN the POST /api/v1/products/ endpoint is called
        THEN the product should be created successfully (backward compatibility)
        """
        # Act
        response = client.post(
            "/api/v1/products/",
            json=sample_product_data,
            headers={"X-API-Key": "test-admin-key"}
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED

    def test_jwt_token_takes_precedence_over_api_key(self, client, sample_product_data):
        """
        GIVEN both JWT token and API key provided
        WHEN the POST /api/v1/products/ endpoint is called
        THEN JWT authentication should be used (takes precedence)
        """
        # Arrange
        valid_token = create_test_jwt(user_id="jwt-user", role="ADMIN")

        # Act - Provide both JWT and API key
        response = client.post(
            "/api/v1/products/",
            json=sample_product_data,
            headers={
                "Authorization": f"Bearer {valid_token}",
                "X-API-Key": "test-admin-key"
            }
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED

    def test_invalid_api_key_with_valid_jwt_succeeds(self, client, sample_product_data):
        """
        GIVEN a valid JWT token and an invalid API key
        WHEN the POST /api/v1/products/ endpoint is called
        THEN the request should succeed (JWT takes precedence)
        """
        # Arrange
        valid_token = create_test_jwt(user_id="jwt-user", role="ADMIN")

        # Act
        response = client.post(
            "/api/v1/products/",
            json=sample_product_data,
            headers={
                "Authorization": f"Bearer {valid_token}",
                "X-API-Key": "wrong-api-key"
            }
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED

    def test_invalid_jwt_with_valid_api_key_fails(self, client, sample_product_data):
        """
        GIVEN an invalid JWT token and a valid API key
        WHEN the POST /api/v1/products/ endpoint is called
        THEN the request should fail (JWT is checked first)
        """
        # Arrange
        client.set_auth(None)
        invalid_token = "invalid.jwt.token"

        try:
            # Act
            response = client.post(
                "/api/v1/products/",
                json=sample_product_data,
                headers={
                    "Authorization": f"Bearer {invalid_token}",
                    "X-API-Key": "test-admin-key"
                }
            )

            # Assert
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
        finally:
            client.set_auth("test-admin-key")


class TestJWTTokenValidation:
    """
    Test suite for JWT token validation edge cases.

    Verifies proper handling of malformed and missing token fields.
    """

    def test_token_without_sub_field_is_rejected(self, client, sample_product_data):
        """
        GIVEN a JWT token missing the 'sub' (user ID) field
        WHEN the POST /api/v1/products/ endpoint is called
        THEN a 401 Unauthorized response should be returned
        """
        # Arrange
        client.set_auth(None)
        payload = {
            "role": "ADMIN",
            "email": "test@example.com",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        try:
            # Act
            response = client.post(
                "/api/v1/products/",
                json=sample_product_data,
                headers={"Authorization": f"Bearer {token}"}
            )

            # Assert
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "missing user identifier" in response.json()["detail"]
        finally:
            client.set_auth("test-admin-key")

    def test_token_with_wrong_algorithm_is_rejected(self, client, sample_product_data):
        """
        GIVEN a JWT token signed with a different algorithm
        WHEN the POST /api/v1/products/ endpoint is called
        THEN a 401 Unauthorized response should be returned
        """
        # Arrange
        client.set_auth(None)
        payload = {
            "sub": "admin-user",
            "role": "ADMIN",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        # Use HS512 instead of HS256
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS512")

        try:
            # Act
            response = client.post(
                "/api/v1/products/",
                json=sample_product_data,
                headers={"Authorization": f"Bearer {token}"}
            )

            # Assert
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
        finally:
            client.set_auth("test-admin-key")

    def test_token_with_wrong_secret_is_rejected(self, client, sample_product_data):
        """
        GIVEN a JWT token signed with a different secret key
        WHEN the POST /api/v1/products/ endpoint is called
        THEN a 401 Unauthorized response should be returned
        """
        # Arrange
        client.set_auth(None)
        payload = {
            "sub": "admin-user",
            "role": "ADMIN",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, "wrong-secret-key", algorithm="HS256")

        try:
            # Act
            response = client.post(
                "/api/v1/products/",
                json=sample_product_data,
                headers={"Authorization": f"Bearer {token}"}
            )

            # Assert
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
        finally:
            client.set_auth("test-admin-key")


class TestMultipleEndpointsWithJWT:
    """
    Test suite to verify JWT auth works across different admin endpoints.

    Ensures consistent authentication behavior across the API.
    """

    def test_update_product_with_jwt_token(self, client, sample_product):
        """
        GIVEN a valid JWT token with ADMIN role
        WHEN the PUT /api/v1/products/{id} endpoint is called
        THEN the product should be updated successfully
        """
        # Arrange
        token = create_test_jwt(user_id="admin-user", role="ADMIN")
        update_data = {"name": "Updated via JWT"}

        # Act
        response = client.put(
            f"/api/v1/products/{sample_product.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == "Updated via JWT"

    def test_delete_product_with_jwt_token(self, client, sample_product):
        """
        GIVEN a valid JWT token with ADMIN role
        WHEN the DELETE /api/v1/products/{id} endpoint is called
        THEN the product should be deleted successfully
        """
        # Arrange
        token = create_test_jwt(user_id="admin-user", role="ADMIN")

        # Act
        response = client.delete(
            f"/api/v1/products/{sample_product.id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_create_template_with_jwt_token(self, client, sample_product):
        """
        GIVEN a valid JWT token with ADMIN role
        WHEN the POST /api/v1/templates/ endpoint is called
        THEN the template should be created successfully
        """
        # Arrange
        token = create_test_jwt(user_id="admin-user", role="ADMIN")
        template_data = {
            "product_id": str(sample_product.id),
            "version": 2,
            "definition": {"zones": {"text_1": {"type": "text"}}},
            "is_default": False,
            "customization_zones": [
                {
                    "key": "text_1",
                    "type": "text",
                    "config": {"max_length": 100},
                    "order_index": 0
                }
            ]
        }

        # Act
        response = client.post(
            "/api/v1/templates/",
            json=template_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED

    def test_update_template_with_user_role_fails(self, client, sample_template):
        """
        GIVEN a valid JWT token with USER role (not ADMIN)
        WHEN the PUT /api/v1/templates/{id} endpoint is called
        THEN a 403 Forbidden response should be returned
        """
        # Arrange
        client.set_auth(None)
        user_token = create_test_jwt(user_id="regular-user", role="USER")
        update_data = {"version": 3}

        try:
            # Act
            response = client.put(
                f"/api/v1/templates/{sample_template.id}",
                json=update_data,
                headers={"Authorization": f"Bearer {user_token}"}
            )

            # Assert
            assert response.status_code == status.HTTP_403_FORBIDDEN
        finally:
            client.set_auth("test-admin-key")


class TestPublicEndpointsWithOptionalAuth:
    """
    Test suite for public endpoints that don't require authentication.

    Verifies read-only endpoints work without auth (backward compatibility).
    """

    def test_get_products_without_auth_succeeds(self, client, sample_product):
        """
        GIVEN no authentication
        WHEN the GET /api/v1/products/ endpoint is called
        THEN the products should be returned successfully
        """
        # Arrange
        client.set_auth(None)

        try:
            # Act
            response = client.get("/api/v1/products/")

            # Assert
            assert response.status_code == status.HTTP_200_OK
            assert isinstance(response.json(), list)
        finally:
            client.set_auth("test-admin-key")

    def test_get_product_by_id_without_auth_succeeds(self, client, sample_product):
        """
        GIVEN no authentication
        WHEN the GET /api/v1/products/{id} endpoint is called
        THEN the product should be returned successfully
        """
        # Arrange
        client.set_auth(None)

        try:
            # Act
            response = client.get(f"/api/v1/products/{sample_product.id}")

            # Assert
            assert response.status_code == status.HTTP_200_OK
            assert response.json()["id"] == str(sample_product.id)
        finally:
            client.set_auth("test-admin-key")
