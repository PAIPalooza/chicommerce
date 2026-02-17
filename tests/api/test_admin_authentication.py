"""
Integration tests for API Key Authentication on Admin Endpoints.

Following BDD (Behavior-Driven Development) patterns and TDD principles
to verify API key authentication requirements per GitHub Issue #16.

Security Requirements:
- Admin endpoints require X-API-Key header
- 401 returned if key missing
- 403 returned if key invalid
- Valid key grants access
"""
import pytest
from fastapi import status
from uuid import uuid4


class TestAdminAuthenticationSecurity:
    """
    Test suite for API key authentication security on admin endpoints.

    Following BDD pattern with describe/it syntax via descriptive test names.
    Tests verify that all admin endpoints properly enforce API key authentication.
    """

    # --- Product Admin Endpoints ---

    def test_create_product_requires_api_key_header(self, client, sample_product_data):
        """
        GIVEN valid product data but no X-API-Key header
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
            assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
                f"Expected 401, got {response.status_code}. Response: {response.text}"
            assert "API key is required" in response.json()["detail"]
        finally:
            # Restore authentication for other tests
            client.set_auth("test-admin-key")

    def test_create_product_rejects_invalid_api_key(self, client, sample_product_data):
        """
        GIVEN valid product data but an invalid X-API-Key header
        WHEN the POST /api/v1/products/ endpoint is called
        THEN a 403 Forbidden response should be returned
        """
        # Arrange - Remove authentication
        client.set_auth(None)

        try:
            # Act
            response = client.post(
                "/api/v1/products/",
                json=sample_product_data,
                headers={"X-API-Key": "invalid-key-12345"}
            )

            # Assert
            assert response.status_code == status.HTTP_403_FORBIDDEN, \
                f"Expected 403, got {response.status_code}. Response: {response.text}"
            assert "Invalid API Key" in response.json()["detail"]
        finally:
            # Restore authentication
            client.set_auth("test-admin-key")

    def test_create_product_accepts_valid_api_key(self, client, sample_product_data):
        """
        GIVEN valid product data and a valid X-API-Key header
        WHEN the POST /api/v1/products/ endpoint is called
        THEN the product should be created successfully (201)
        """
        # Act
        response = client.post(
            "/api/v1/products/",
            json=sample_product_data,
            headers={"X-API-Key": "test-admin-key"}
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == sample_product_data["name"]
        assert "id" in data

    def test_update_product_requires_api_key_header(self, client, sample_product):
        """
        GIVEN an existing product and valid update data but no X-API-Key header
        WHEN the PUT /api/v1/products/{id} endpoint is called
        THEN a 401 Unauthorized response should be returned
        """
        # Arrange
        client.set_auth(None)
        update_data = {"name": "Updated Product"}

        try:
            # Act
            response = client.put(
                f"/api/v1/products/{sample_product.id}",
                json=update_data
            )

            # Assert
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "API key is required" in response.json()["detail"]
        finally:
            client.set_auth("test-admin-key")

    def test_update_product_rejects_invalid_api_key(self, client, sample_product):
        """
        GIVEN an existing product and valid update data but invalid X-API-Key
        WHEN the PUT /api/v1/products/{id} endpoint is called
        THEN a 403 Forbidden response should be returned
        """
        # Arrange
        client.set_auth(None)
        update_data = {"name": "Updated Product"}

        try:
            # Act
            response = client.put(
                f"/api/v1/products/{sample_product.id}",
                json=update_data,
                headers={"X-API-Key": "wrong-api-key"}
            )

            # Assert
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert "Invalid API Key" in response.json()["detail"]
        finally:
            client.set_auth("test-admin-key")

    def test_update_product_accepts_valid_api_key(self, client, sample_product):
        """
        GIVEN an existing product, valid update data, and valid X-API-Key
        WHEN the PUT /api/v1/products/{id} endpoint is called
        THEN the product should be updated successfully (200)
        """
        # Arrange
        update_data = {"name": "Updated Product", "base_price": 29.99}

        # Act
        response = client.put(
            f"/api/v1/products/{sample_product.id}",
            json=update_data,
            headers={"X-API-Key": "test-admin-key"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Product"
        assert float(data["base_price"]) == 29.99

    def test_delete_product_requires_api_key_header(self, client, sample_product):
        """
        GIVEN an existing product but no X-API-Key header
        WHEN the DELETE /api/v1/products/{id} endpoint is called
        THEN a 401 Unauthorized response should be returned
        """
        # Arrange
        client.set_auth(None)

        try:
            # Act
            response = client.delete(f"/api/v1/products/{sample_product.id}")

            # Assert
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "API key is required" in response.json()["detail"]
        finally:
            client.set_auth("test-admin-key")

    def test_delete_product_rejects_invalid_api_key(self, client, sample_product):
        """
        GIVEN an existing product but invalid X-API-Key header
        WHEN the DELETE /api/v1/products/{id} endpoint is called
        THEN a 403 Forbidden response should be returned
        """
        # Arrange
        client.set_auth(None)

        try:
            # Act
            response = client.delete(
                f"/api/v1/products/{sample_product.id}",
                headers={"X-API-Key": "invalid-delete-key"}
            )

            # Assert
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert "Invalid API Key" in response.json()["detail"]
        finally:
            client.set_auth("test-admin-key")

    def test_delete_product_accepts_valid_api_key(self, client, sample_product):
        """
        GIVEN an existing product and valid X-API-Key header
        WHEN the DELETE /api/v1/products/{id} endpoint is called
        THEN the product should be deleted successfully (204)
        """
        # Act
        response = client.delete(
            f"/api/v1/products/{sample_product.id}",
            headers={"X-API-Key": "test-admin-key"}
        )

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT

    # --- Template Admin Endpoints ---

    def test_create_template_requires_api_key_header(self, client, sample_product):
        """
        GIVEN valid template data but no X-API-Key header
        WHEN the POST /api/v1/templates/ endpoint is called
        THEN a 401 Unauthorized response should be returned
        """
        # Arrange
        client.set_auth(None)
        template_data = {
            "product_id": str(sample_product.id),
            "version": 1,
            "definition": {"zones": {"text_1": {"type": "text"}}},
            "is_default": True
        }

        try:
            # Act
            response = client.post(
                "/api/v1/templates/",
                json=template_data
            )

            # Assert
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "API key is required" in response.json()["detail"]
        finally:
            client.set_auth("test-admin-key")

    def test_create_template_rejects_invalid_api_key(self, client, sample_product):
        """
        GIVEN valid template data but invalid X-API-Key header
        WHEN the POST /api/v1/templates/ endpoint is called
        THEN a 403 Forbidden response should be returned
        """
        # Arrange
        client.set_auth(None)
        template_data = {
            "product_id": str(sample_product.id),
            "version": 1,
            "definition": {"zones": {"text_1": {"type": "text"}}},
            "is_default": True
        }

        try:
            # Act
            response = client.post(
                "/api/v1/templates/",
                json=template_data,
                headers={"X-API-Key": "bad-template-key"}
            )

            # Assert
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert "Invalid API Key" in response.json()["detail"]
        finally:
            client.set_auth("test-admin-key")

    def test_create_template_accepts_valid_api_key(self, client, sample_product):
        """
        GIVEN valid template data and valid X-API-Key header
        WHEN the POST /api/v1/templates/ endpoint is called
        THEN the template should be created successfully (201)
        """
        # Arrange
        template_data = {
            "product_id": str(sample_product.id),
            "version": 1,
            "definition": {"zones": {"text_1": {"type": "text"}}},
            "is_default": True,
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
            headers={"X-API-Key": "test-admin-key"}
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["version"] == 1
        assert "id" in data

    def test_update_template_requires_api_key_header(self, client, sample_template):
        """
        GIVEN an existing template and valid update data but no X-API-Key header
        WHEN the PUT /api/v1/templates/{id} endpoint is called
        THEN a 401 Unauthorized response should be returned
        """
        # Arrange
        client.set_auth(None)
        update_data = {"version": 2}

        try:
            # Act
            response = client.put(
                f"/api/v1/templates/{sample_template.id}",
                json=update_data
            )

            # Assert
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "API key is required" in response.json()["detail"]
        finally:
            client.set_auth("test-admin-key")

    def test_update_template_rejects_invalid_api_key(self, client, sample_template):
        """
        GIVEN an existing template and valid update data but invalid X-API-Key
        WHEN the PUT /api/v1/templates/{id} endpoint is called
        THEN a 403 Forbidden response should be returned
        """
        # Arrange
        client.set_auth(None)
        update_data = {"version": 2}

        try:
            # Act
            response = client.put(
                f"/api/v1/templates/{sample_template.id}",
                json=update_data,
                headers={"X-API-Key": "incorrect-template-key"}
            )

            # Assert
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert "Invalid API Key" in response.json()["detail"]
        finally:
            client.set_auth("test-admin-key")

    def test_update_template_accepts_valid_api_key(self, client, sample_template):
        """
        GIVEN an existing template, valid update data, and valid X-API-Key
        WHEN the PUT /api/v1/templates/{id} endpoint is called
        THEN the template should be updated successfully (200)
        """
        # Arrange - Only update is_default to avoid version conflicts
        update_data = {
            "is_default": False
        }

        # Act
        response = client.put(
            f"/api/v1/templates/{sample_template.id}",
            json=update_data,
            headers={"X-API-Key": "test-admin-key"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_default"] == False

    def test_delete_template_requires_api_key_header(self, client, db_session, sample_template):
        """
        GIVEN an existing template but no X-API-Key header
        WHEN the DELETE /api/v1/templates/{id} endpoint is called
        THEN a 401 Unauthorized response should be returned
        """
        # Arrange - Create another template so we can delete the first
        from app.models.template import Template

        another_template = Template(
            product_id=sample_template.product_id,
            version=2,
            definition={"zones": {"text_2": {"type": "text"}}},
            is_default=False
        )
        db_session.add(another_template)
        db_session.commit()

        client.set_auth(None)

        try:
            # Act
            response = client.delete(f"/api/v1/templates/{sample_template.id}")

            # Assert
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "API key is required" in response.json()["detail"]
        finally:
            client.set_auth("test-admin-key")

    def test_delete_template_rejects_invalid_api_key(self, client, db_session, sample_template):
        """
        GIVEN an existing template but invalid X-API-Key header
        WHEN the DELETE /api/v1/templates/{id} endpoint is called
        THEN a 403 Forbidden response should be returned
        """
        # Arrange - Create another template so we can delete the first
        from app.models.template import Template

        another_template = Template(
            product_id=sample_template.product_id,
            version=2,
            definition={"zones": {"text_2": {"type": "text"}}},
            is_default=False
        )
        db_session.add(another_template)
        db_session.commit()

        client.set_auth(None)

        try:
            # Act
            response = client.delete(
                f"/api/v1/templates/{sample_template.id}",
                headers={"X-API-Key": "wrong-delete-template-key"}
            )

            # Assert
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert "Invalid API Key" in response.json()["detail"]
        finally:
            client.set_auth("test-admin-key")

    def test_delete_template_accepts_valid_api_key(self, client, db_session, sample_template):
        """
        GIVEN an existing template and valid X-API-Key header
        WHEN the DELETE /api/v1/templates/{id} endpoint is called
        THEN the template should be deleted successfully (204)
        """
        # Arrange - Create another template so we can delete the first
        from app.models.template import Template

        another_template = Template(
            product_id=sample_template.product_id,
            version=2,
            definition={"zones": {"text_2": {"type": "text"}}},
            is_default=False
        )
        db_session.add(another_template)
        db_session.commit()

        # Act
        response = client.delete(
            f"/api/v1/templates/{sample_template.id}",
            headers={"X-API-Key": "test-admin-key"}
        )

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT

    # --- Read-Only Endpoints Should Not Require Authentication ---

    def test_get_products_does_not_require_api_key(self, client, db_session, sample_product_data):
        """
        GIVEN no X-API-Key header
        WHEN the GET /api/v1/products/ endpoint is called
        THEN the products should be returned successfully (200)
        """
        # Arrange - Create a product directly in the DB
        from app.models.product import Product

        product = Product(**sample_product_data)
        db_session.add(product)
        db_session.commit()

        client.set_auth(None)

        try:
            # Act
            response = client.get("/api/v1/products/")

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert isinstance(data, list)
        finally:
            client.set_auth("test-admin-key")

    def test_get_product_by_id_does_not_require_api_key(self, client, sample_product):
        """
        GIVEN no X-API-Key header
        WHEN the GET /api/v1/products/{id} endpoint is called
        THEN the product should be returned successfully (200)
        """
        # Arrange
        client.set_auth(None)

        try:
            # Act
            response = client.get(f"/api/v1/products/{sample_product.id}")

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["id"] == str(sample_product.id)
        finally:
            client.set_auth("test-admin-key")

    def test_get_templates_does_not_require_api_key(self, client, sample_template):
        """
        GIVEN no X-API-Key header
        WHEN the GET /api/v1/templates/ endpoint is called with product_id
        THEN the templates should be returned successfully (200)
        """
        # Arrange
        client.set_auth(None)

        try:
            # Act
            response = client.get(
                f"/api/v1/templates/?product_id={sample_template.product_id}"
            )

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert isinstance(data, list)
        finally:
            client.set_auth("test-admin-key")

    def test_get_template_by_id_does_not_require_api_key(self, client, sample_template):
        """
        GIVEN no X-API-Key header
        WHEN the GET /api/v1/templates/{id} endpoint is called
        THEN the template should be returned successfully (200)
        """
        # Arrange
        client.set_auth(None)

        try:
            # Act
            response = client.get(f"/api/v1/templates/{sample_template.id}")

            # Assert
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["id"] == str(sample_template.id)
        finally:
            client.set_auth("test-admin-key")


class TestAPIKeySecurityBestPractices:
    """
    Test suite for API key security best practices.

    Ensures the authentication system follows security best practices.
    """

    def test_api_key_is_case_sensitive(self, client, sample_product_data):
        """
        GIVEN an API key with mixed case
        WHEN different case variations are used
        THEN only the exact match should be accepted
        """
        # Arrange
        client.set_auth(None)

        try:
            # Act - Try uppercase version of the test key
            response = client.post(
                "/api/v1/products/",
                json=sample_product_data,
                headers={"X-API-Key": "TEST-ADMIN-KEY"}  # Uppercase
            )

            # Assert - Should fail since API keys are case-sensitive
            assert response.status_code == status.HTTP_403_FORBIDDEN
        finally:
            client.set_auth("test-admin-key")

    def test_api_key_header_name_is_case_insensitive(self, client, db_session, sample_product_data):
        """
        GIVEN a valid API key
        WHEN the header name uses different casing (HTTP headers are case-insensitive)
        THEN the request should be accepted
        """
        # Arrange - Ensure clean DB state
        from app.models.product import Product
        db_session.query(Product).delete()
        db_session.commit()

        client.set_auth(None)

        try:
            # Act - Try different header name casing
            response = client.post(
                "/api/v1/products/",
                json=sample_product_data,
                headers={"x-api-key": "test-admin-key"}  # lowercase header name
            )

            # Assert - Should succeed (HTTP headers are case-insensitive)
            assert response.status_code == status.HTTP_201_CREATED
        finally:
            client.set_auth("test-admin-key")

    def test_empty_api_key_is_rejected(self, client, sample_product_data):
        """
        GIVEN an empty string as API key
        WHEN the POST /api/v1/products/ endpoint is called
        THEN a 401 or 403 response should be returned
        """
        # Arrange
        client.set_auth(None)

        try:
            # Act
            response = client.post(
                "/api/v1/products/",
                json=sample_product_data,
                headers={"X-API-Key": ""}
            )

            # Assert - Empty key should be rejected
            assert response.status_code in [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN
            ]
        finally:
            client.set_auth("test-admin-key")

    def test_whitespace_only_api_key_is_rejected(self, client, sample_product_data):
        """
        GIVEN an API key containing only whitespace
        WHEN the POST /api/v1/products/ endpoint is called
        THEN a 403 Forbidden response should be returned
        """
        # Arrange
        client.set_auth(None)

        try:
            # Act
            response = client.post(
                "/api/v1/products/",
                json=sample_product_data,
                headers={"X-API-Key": "   "}
            )

            # Assert
            assert response.status_code == status.HTTP_403_FORBIDDEN
        finally:
            client.set_auth("test-admin-key")

    def test_api_key_with_special_characters_is_handled_correctly(self, client, sample_product_data):
        """
        GIVEN an API key with special characters
        WHEN the key doesn't match the configured admin key
        THEN a 403 Forbidden response should be returned
        """
        # Arrange
        client.set_auth(None)
        special_chars_key = "test!@#$%^&*()_+-=[]{}|;:',.<>?/`~"

        try:
            # Act
            response = client.post(
                "/api/v1/products/",
                json=sample_product_data,
                headers={"X-API-Key": special_chars_key}
            )

            # Assert
            assert response.status_code == status.HTTP_403_FORBIDDEN
        finally:
            client.set_auth("test-admin-key")
