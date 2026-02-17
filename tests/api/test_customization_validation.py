"""
Integration tests for Customization Session Validation API endpoints.

Following BDD (Behavior-Driven Development) patterns and TDD principles.
Tests are written FIRST to define expected behavior.
"""
import pytest
from uuid import uuid4, UUID
from fastapi import status

from app.models.product import Product
from app.models.template import Template, CustomizationZone


class TestCustomizationSessionValidation:
    """
    Test suite for Customization Session Validation API endpoints.

    Following BDD pattern with GIVEN-WHEN-THEN structure in test method names
    and docstrings. These tests validate that customization inputs respect
    template constraints.
    """

    # --- Text Length Validation ---

    def test_update_session_with_valid_text_length_succeeds(self, client, db_session, sample_product, sample_template):
        """
        GIVEN a customization session and text input within max_length constraint
        WHEN the PATCH /customization-sessions/{product_id} endpoint is called
        THEN the session should be updated successfully
        """
        # Arrange - create a session first
        session_id = "test-session-123"
        create_response = client.post(
            "/api/v1/customization-sessions",
            json={
                "product_id": str(sample_product.id),
                "session_id": session_id,
                "customization_data": {}
            }
        )
        assert create_response.status_code == status.HTTP_201_CREATED

        # Act - update with valid text (within 100 char limit from sample_template)
        update_data = {
            "customization_data": {
                "text_1": "This is valid text within the limit"
            }
        }

        response = client.patch(
            f"/api/v1/customization-sessions/{sample_product.id}",
            json=update_data,
            cookies={"session_id": session_id}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["customization_data"]["text_1"] == "This is valid text within the limit"

    def test_update_session_with_text_exceeding_max_length_fails(self, client, db_session, sample_product, sample_template):
        """
        GIVEN a customization session and text input exceeding max_length constraint
        WHEN the PATCH /customization-sessions/{product_id} endpoint is called
        THEN a 400 Bad Request with detailed error should be returned
        """
        # Arrange - create a session first
        session_id = "test-session-124"
        create_response = client.post(
            "/api/v1/customization-sessions",
            json={
                "product_id": str(sample_product.id),
                "session_id": session_id,
                "customization_data": {}
            }
        )
        assert create_response.status_code == status.HTTP_201_CREATED

        # Act - update with text exceeding 100 char limit
        long_text = "x" * 101
        update_data = {
            "customization_data": {
                "text_1": long_text
            }
        }

        response = client.patch(
            f"/api/v1/customization-sessions/{sample_product.id}",
            json=update_data,
            cookies={"session_id": session_id}
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error_data = response.json()
        assert "detail" in error_data
        assert "text_1" in error_data["detail"]
        assert "max_length" in error_data["detail"].lower() or "100" in error_data["detail"]

    def test_update_session_with_empty_text_succeeds(self, client, db_session, sample_product, sample_template):
        """
        GIVEN a customization session and empty text input
        WHEN the PATCH /customization-sessions/{product_id} endpoint is called
        THEN the session should be updated successfully (empty is valid)
        """
        # Arrange
        session_id = "test-session-125"
        create_response = client.post(
            "/api/v1/customization-sessions",
            json={
                "product_id": str(sample_product.id),
                "session_id": session_id,
                "customization_data": {}
            }
        )
        assert create_response.status_code == status.HTTP_201_CREATED

        # Act
        update_data = {
            "customization_data": {
                "text_1": ""
            }
        }

        response = client.patch(
            f"/api/v1/customization-sessions/{sample_product.id}",
            json=update_data,
            cookies={"session_id": session_id}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["customization_data"]["text_1"] == ""

    # --- Image Format Validation ---

    def test_update_session_with_valid_image_format_succeeds(self, client, db_session, sample_product, sample_template):
        """
        GIVEN a customization session and image with valid format
        WHEN the PATCH /customization-sessions/{product_id} endpoint is called
        THEN the session should be updated successfully
        """
        # Arrange
        session_id = "test-session-126"
        create_response = client.post(
            "/api/v1/customization-sessions",
            json={
                "product_id": str(sample_product.id),
                "session_id": session_id,
                "customization_data": {}
            }
        )
        assert create_response.status_code == status.HTTP_201_CREATED

        # Act - image_1 accepts png and jpg formats
        update_data = {
            "customization_data": {
                "image_1": {
                    "url": "https://example.com/image.png",
                    "format": "png"
                }
            }
        }

        response = client.patch(
            f"/api/v1/customization-sessions/{sample_product.id}",
            json=update_data,
            cookies={"session_id": session_id}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["customization_data"]["image_1"]["format"] == "png"

    def test_update_session_with_invalid_image_format_fails(self, client, db_session, sample_product, sample_template):
        """
        GIVEN a customization session and image with invalid format
        WHEN the PATCH /customization-sessions/{product_id} endpoint is called
        THEN a 400 Bad Request with detailed error should be returned
        """
        # Arrange
        session_id = "test-session-127"
        create_response = client.post(
            "/api/v1/customization-sessions",
            json={
                "product_id": str(sample_product.id),
                "session_id": session_id,
                "customization_data": {}
            }
        )
        assert create_response.status_code == status.HTTP_201_CREATED

        # Act - image_1 only accepts png and jpg
        update_data = {
            "customization_data": {
                "image_1": {
                    "url": "https://example.com/image.gif",
                    "format": "gif"
                }
            }
        }

        response = client.patch(
            f"/api/v1/customization-sessions/{sample_product.id}",
            json=update_data,
            cookies={"session_id": session_id}
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error_data = response.json()
        assert "detail" in error_data
        assert "image_1" in error_data["detail"]
        assert "format" in error_data["detail"].lower()

    # --- Unknown Zone Validation ---

    def test_update_session_with_unknown_zone_fails(self, client, db_session, sample_product, sample_template):
        """
        GIVEN a customization session and data for unknown zone
        WHEN the PATCH /customization-sessions/{product_id} endpoint is called
        THEN a 400 Bad Request with detailed error should be returned
        """
        # Arrange
        session_id = "test-session-128"
        create_response = client.post(
            "/api/v1/customization-sessions",
            json={
                "product_id": str(sample_product.id),
                "session_id": session_id,
                "customization_data": {}
            }
        )
        assert create_response.status_code == status.HTTP_201_CREATED

        # Act - provide data for non-existent zone
        update_data = {
            "customization_data": {
                "unknown_zone": "some data"
            }
        }

        response = client.patch(
            f"/api/v1/customization-sessions/{sample_product.id}",
            json=update_data,
            cookies={"session_id": session_id}
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error_data = response.json()
        assert "detail" in error_data
        assert "unknown_zone" in error_data["detail"]

    # --- Multiple Zone Validation ---

    def test_update_session_with_multiple_valid_zones_succeeds(self, client, db_session, sample_product, sample_template):
        """
        GIVEN a customization session and valid data for multiple zones
        WHEN the PATCH /customization-sessions/{product_id} endpoint is called
        THEN the session should be updated successfully
        """
        # Arrange
        session_id = "test-session-129"
        create_response = client.post(
            "/api/v1/customization-sessions",
            json={
                "product_id": str(sample_product.id),
                "session_id": session_id,
                "customization_data": {}
            }
        )
        assert create_response.status_code == status.HTTP_201_CREATED

        # Act - provide valid data for both zones
        update_data = {
            "customization_data": {
                "text_1": "Valid text",
                "image_1": {
                    "url": "https://example.com/image.jpg",
                    "format": "jpg"
                }
            }
        }

        response = client.patch(
            f"/api/v1/customization-sessions/{sample_product.id}",
            json=update_data,
            cookies={"session_id": session_id}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["customization_data"]["text_1"] == "Valid text"
        assert data["customization_data"]["image_1"]["format"] == "jpg"

    def test_update_session_with_mixed_valid_invalid_zones_fails(self, client, db_session, sample_product, sample_template):
        """
        GIVEN a customization session with one valid and one invalid zone
        WHEN the PATCH /customization-sessions/{product_id} endpoint is called
        THEN a 400 Bad Request with detailed errors should be returned
        """
        # Arrange
        session_id = "test-session-130"
        create_response = client.post(
            "/api/v1/customization-sessions",
            json={
                "product_id": str(sample_product.id),
                "session_id": session_id,
                "customization_data": {}
            }
        )
        assert create_response.status_code == status.HTTP_201_CREATED

        # Act - one valid, one invalid
        update_data = {
            "customization_data": {
                "text_1": "x" * 101,  # Invalid - exceeds max_length
                "image_1": {
                    "url": "https://example.com/image.png",
                    "format": "png"  # Valid
                }
            }
        }

        response = client.patch(
            f"/api/v1/customization-sessions/{sample_product.id}",
            json=update_data,
            cookies={"session_id": session_id}
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error_data = response.json()
        assert "detail" in error_data
        assert "text_1" in error_data["detail"]

    # --- Session Not Found Validation ---

    def test_update_nonexistent_session_fails(self, client, db_session, sample_product, sample_template):
        """
        GIVEN no existing customization session
        WHEN the PATCH /customization-sessions/{product_id} endpoint is called
        THEN a 404 Not Found should be returned
        """
        # Act - try to update without creating session first
        update_data = {
            "customization_data": {
                "text_1": "some text"
            }
        }

        response = client.patch(
            f"/api/v1/customization-sessions/{sample_product.id}",
            json=update_data,
            cookies={"session_id": "nonexistent-session"}
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    # --- Product Without Template Validation ---

    def test_update_session_for_product_without_template_fails(self, client, db_session):
        """
        GIVEN a product without a default template
        WHEN the PATCH /customization-sessions/{product_id} endpoint is called
        THEN a 400 Bad Request should be returned
        """
        # Arrange - create product without template
        product = Product(
            name="Product Without Template",
            description="Test product",
            base_price=10.00,
            is_active=True
        )
        db_session.add(product)
        db_session.commit()
        db_session.refresh(product)

        # Create session
        session_id = "test-session-131"
        create_response = client.post(
            "/api/v1/customization-sessions",
            json={
                "product_id": str(product.id),
                "session_id": session_id,
                "customization_data": {}
            }
        )
        assert create_response.status_code == status.HTTP_201_CREATED

        # Act - try to update
        update_data = {
            "customization_data": {
                "some_zone": "some data"
            }
        }

        response = client.patch(
            f"/api/v1/customization-sessions/{product.id}",
            json=update_data,
            cookies={"session_id": session_id}
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error_data = response.json()
        assert "template" in error_data["detail"].lower()

    # --- Complex Template Validation ---

    def test_update_session_with_color_palette_validation(self, client, db_session, sample_product):
        """
        GIVEN a template with color zone and palette constraint
        WHEN updating with valid color from palette
        THEN the session should be updated successfully
        """
        # Arrange - create template with color zone
        template = Template(
            product_id=sample_product.id,
            version=2,
            definition={
                "zones": {
                    "color_primary": {
                        "type": "color",
                        "palette": ["#FF0000", "#00FF00", "#0000FF"]
                    }
                }
            },
            is_default=True
        )
        db_session.add(template)
        db_session.flush()

        zone = CustomizationZone(
            template_id=template.id,
            key="color_primary",
            type="color",
            config={"palette": ["#FF0000", "#00FF00", "#0000FF"]},
            order_index=0
        )
        db_session.add(zone)
        db_session.commit()

        # Create session
        session_id = "test-session-132"
        create_response = client.post(
            "/api/v1/customization-sessions",
            json={
                "product_id": str(sample_product.id),
                "session_id": session_id,
                "customization_data": {}
            }
        )
        assert create_response.status_code == status.HTTP_201_CREATED

        # Act - update with valid color
        update_data = {
            "customization_data": {
                "color_primary": "#FF0000"
            }
        }

        response = client.patch(
            f"/api/v1/customization-sessions/{sample_product.id}",
            json=update_data,
            cookies={"session_id": session_id}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["customization_data"]["color_primary"] == "#FF0000"

    def test_update_session_with_invalid_color_from_palette_fails(self, client, db_session, sample_product):
        """
        GIVEN a template with color zone and palette constraint
        WHEN updating with color not in palette
        THEN a 400 Bad Request should be returned
        """
        # Arrange - create template with color zone
        template = Template(
            product_id=sample_product.id,
            version=3,
            definition={
                "zones": {
                    "color_primary": {
                        "type": "color",
                        "palette": ["#FF0000", "#00FF00", "#0000FF"]
                    }
                }
            },
            is_default=True
        )
        db_session.add(template)
        db_session.flush()

        zone = CustomizationZone(
            template_id=template.id,
            key="color_primary",
            type="color",
            config={"palette": ["#FF0000", "#00FF00", "#0000FF"]},
            order_index=0
        )
        db_session.add(zone)
        db_session.commit()

        # Create session
        session_id = "test-session-133"
        create_response = client.post(
            "/api/v1/customization-sessions",
            json={
                "product_id": str(sample_product.id),
                "session_id": session_id,
                "customization_data": {}
            }
        )
        assert create_response.status_code == status.HTTP_201_CREATED

        # Act - update with invalid color
        update_data = {
            "customization_data": {
                "color_primary": "#FFFFFF"  # Not in palette
            }
        }

        response = client.patch(
            f"/api/v1/customization-sessions/{sample_product.id}",
            json=update_data,
            cookies={"session_id": session_id}
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error_data = response.json()
        assert "detail" in error_data
        assert "color_primary" in error_data["detail"]
        assert "palette" in error_data["detail"].lower()

    # --- No Session Cookie Validation ---

    def test_update_session_without_session_cookie_fails(self, client, db_session, sample_product, sample_template):
        """
        GIVEN no session cookie in request
        WHEN the PATCH /customization-sessions/{product_id} endpoint is called
        THEN a 404 Not Found should be returned
        """
        # Act - try to update without session cookie
        update_data = {
            "customization_data": {
                "text_1": "some text"
            }
        }

        response = client.patch(
            f"/api/v1/customization-sessions/{sample_product.id}",
            json=update_data
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
