"""
Integration tests for Session API endpoints.

Following BDD (Behavior-Driven Development) patterns and TDD principles.
Tests for creating and retrieving customization sessions.
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from fastapi import status

from app.models.cart import CustomizationSession
from app.models.product import Product
from app.models.template import Template, CustomizationZone


class TestPostSessionsEndpoint:
    """Test suite for POST /api/v1/sessions endpoint (Issue #5)."""

    def test_create_session_returns_201_with_valid_data(self, client, sample_product, sample_template):
        """
        GIVEN a valid product_id and template_id
        WHEN POST /api/v1/sessions is called
        THEN it should return 201 status with session data
        """
        # Arrange
        payload = {
            "product_id": str(sample_product.id),
            "template_id": str(sample_template.id)
        }

        # Act
        response = client.post("/api/v1/sessions", json=payload)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "session_id" in data
        assert "session_key" in data
        assert data["product_id"] == str(sample_product.id)
        assert data["template_id"] == str(sample_template.id)
        assert data["options"] == {}

    def test_create_session_generates_unique_session_id(self, client, sample_product, sample_template):
        """
        GIVEN multiple session creation requests
        WHEN POST /api/v1/sessions is called multiple times
        THEN each session should have a unique session_id
        """
        # Arrange
        payload = {
            "product_id": str(sample_product.id),
            "template_id": str(sample_template.id)
        }

        # Act
        response1 = client.post("/api/v1/sessions", json=payload)
        response2 = client.post("/api/v1/sessions", json=payload)

        # Assert
        assert response1.status_code == 201
        assert response2.status_code == 201
        session1 = response1.json()
        session2 = response2.json()
        assert session1["session_id"] != session2["session_id"]

    def test_create_session_generates_unique_session_key(self, client, sample_product, sample_template):
        """
        GIVEN multiple session creation requests
        WHEN POST /api/v1/sessions is called multiple times
        THEN each session should have a unique session_key
        """
        # Arrange
        payload = {
            "product_id": str(sample_product.id),
            "template_id": str(sample_template.id)
        }

        # Act
        response1 = client.post("/api/v1/sessions", json=payload)
        response2 = client.post("/api/v1/sessions", json=payload)

        # Assert
        assert response1.status_code == 201
        assert response2.status_code == 201
        session1 = response1.json()
        session2 = response2.json()
        assert session1["session_key"] != session2["session_key"]

    def test_create_session_key_has_secure_format(self, client, sample_product, sample_template):
        """
        GIVEN a session creation request
        WHEN POST /api/v1/sessions is called
        THEN the session_key should be a secure, URL-safe string
        """
        # Arrange
        payload = {
            "product_id": str(sample_product.id),
            "template_id": str(sample_template.id)
        }

        # Act
        response = client.post("/api/v1/sessions", json=payload)

        # Assert
        assert response.status_code == 201
        session_key = response.json()["session_key"]
        assert len(session_key) >= 32
        assert session_key.startswith("sess_")
        assert all(c.isalnum() or c in "-_" for c in session_key)

    def test_create_session_persists_to_database(self, client, db_session, sample_product, sample_template):
        """
        GIVEN a valid session creation request
        WHEN POST /api/v1/sessions is called
        THEN the session should be persisted in the database
        """
        # Arrange
        payload = {
            "product_id": str(sample_product.id),
            "template_id": str(sample_template.id)
        }

        # Act
        response = client.post("/api/v1/sessions", json=payload)

        # Assert
        assert response.status_code == 201
        session_id = response.json()["session_id"]

        db_session.expire_all()
        session = db_session.query(CustomizationSession).filter_by(id=session_id).first()
        assert session is not None
        assert str(session.product_id) == str(sample_product.id)
        assert str(session.template_id) == str(sample_template.id)
        assert session.options == {}
        assert session.is_active is True

    def test_create_session_returns_422_with_invalid_product_id(self, client, sample_template):
        """
        GIVEN an invalid product_id
        WHEN POST /api/v1/sessions is called
        THEN it should return 422 validation error
        """
        # Arrange
        payload = {
            "product_id": "not-a-valid-uuid",
            "template_id": str(sample_template.id)
        }

        # Act
        response = client.post("/api/v1/sessions", json=payload)

        # Assert
        assert response.status_code == 422

    def test_create_session_returns_404_with_nonexistent_product(self, client, sample_template):
        """
        GIVEN a non-existent product_id
        WHEN POST /api/v1/sessions is called
        THEN it should return 404 not found
        """
        # Arrange
        payload = {
            "product_id": str(uuid4()),
            "template_id": str(sample_template.id)
        }

        # Act
        response = client.post("/api/v1/sessions", json=payload)

        # Assert
        assert response.status_code == 404
        assert "product" in response.json()["detail"].lower()

    def test_create_session_returns_404_with_nonexistent_template(self, client, sample_product):
        """
        GIVEN a non-existent template_id
        WHEN POST /api/v1/sessions is called
        THEN it should return 404 not found
        """
        # Arrange
        payload = {
            "product_id": str(sample_product.id),
            "template_id": str(uuid4())
        }

        # Act
        response = client.post("/api/v1/sessions", json=payload)

        # Assert
        assert response.status_code == 404
        assert "template" in response.json()["detail"].lower()

    def test_create_session_initializes_with_empty_options(self, client, sample_product, sample_template):
        """
        GIVEN a session creation request
        WHEN POST /api/v1/sessions is called
        THEN the session should be initialized with empty options
        """
        # Arrange
        payload = {
            "product_id": str(sample_product.id),
            "template_id": str(sample_template.id)
        }

        # Act
        response = client.post("/api/v1/sessions", json=payload)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["options"] == {}
        assert isinstance(data["options"], dict)


class TestSessionsAPI:
    """
    Test suite for Session API endpoints.

    Following BDD pattern with descriptive test method names.
    """

    # --- GET /sessions/{sessionId} ---

    def test_get_session_returns_session_with_customization_data(
        self, client, db_session, sample_product, sample_template
    ):
        """
        GIVEN a valid session with customization data
        WHEN the GET /sessions/{sessionId} endpoint is called
        THEN the session state with options and template version should be returned
        """
        # Arrange
        session_id = "test-session-123"
        customization_data = {
            "text_1": "Custom Text",
            "image_1": "https://example.com/image.png",
            "color": "blue"
        }

        db_customization_session = CustomizationSession(
            session_id=session_id,
            product_id=sample_product.id,
            customization_data=customization_data,
            is_active=True
        )
        db_session.add(db_customization_session)
        db_session.commit()
        db_session.refresh(db_customization_session)

        # Act
        response = client.get(f"/api/v1/sessions/{session_id}")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["session_id"] == session_id
        assert data["product_id"] == str(sample_product.id)
        assert data["customization_data"] == customization_data
        assert data["template_version"] == sample_template.version
        assert data["is_active"] is True
        assert "created_at" in data
        assert "updated_at" in data

    def test_get_session_returns_404_for_invalid_session(self, client):
        """
        GIVEN an invalid or non-existent session ID
        WHEN the GET /sessions/{sessionId} endpoint is called
        THEN a 404 Not Found response should be returned
        """
        # Arrange
        invalid_session_id = "non-existent-session-id"

        # Act
        response = client.get(f"/api/v1/sessions/{invalid_session_id}")

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in response.json()
        assert "not found" in response.json()["detail"].lower()

    def test_get_session_returns_404_for_expired_session(
        self, client, db_session, sample_product
    ):
        """
        GIVEN an expired session (created more than 30 days ago)
        WHEN the GET /sessions/{sessionId} endpoint is called
        THEN a 404 Not Found response should be returned
        """
        # Arrange
        session_id = "expired-session-123"
        expired_date = datetime.utcnow() - timedelta(days=31)

        # Create a session with an expired timestamp
        db_customization_session = CustomizationSession(
            session_id=session_id,
            product_id=sample_product.id,
            customization_data={"test": "data"},
            is_active=True,
            created_at=expired_date,
            updated_at=expired_date
        )
        db_session.add(db_customization_session)
        db_session.commit()

        # Act
        response = client.get(f"/api/v1/sessions/{session_id}")

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "expired" in response.json()["detail"].lower()

    def test_get_session_returns_404_for_inactive_session(
        self, client, db_session, sample_product
    ):
        """
        GIVEN an inactive session
        WHEN the GET /sessions/{sessionId} endpoint is called
        THEN a 404 Not Found response should be returned
        """
        # Arrange
        session_id = "inactive-session-123"

        db_customization_session = CustomizationSession(
            session_id=session_id,
            product_id=sample_product.id,
            customization_data={"test": "data"},
            is_active=False  # Inactive session
        )
        db_session.add(db_customization_session)
        db_session.commit()

        # Act
        response = client.get(f"/api/v1/sessions/{session_id}")

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    def test_get_session_with_multiple_products_returns_all_sessions(
        self, client, db_session, sample_product, sample_template
    ):
        """
        GIVEN a session with multiple product customizations
        WHEN the GET /sessions/{sessionId} endpoint is called
        THEN all customization sessions for that session should be returned
        """
        # Arrange
        session_id = "multi-product-session"

        # Create another product
        product2 = Product(
            name="Test Product 2",
            description="Another test product",
            base_price=29.99,
            media={},
            is_active=True
        )
        db_session.add(product2)
        db_session.commit()
        db_session.refresh(product2)

        # Create template for product2
        template2 = Template(
            product_id=product2.id,
            version=2,
            definition={"zones": {"text_2": {"type": "text"}}},
            is_default=True
        )
        db_session.add(template2)
        db_session.commit()

        # Create customization sessions for both products
        session1 = CustomizationSession(
            session_id=session_id,
            product_id=sample_product.id,
            customization_data={"text_1": "Product 1 text"},
            is_active=True
        )
        session2 = CustomizationSession(
            session_id=session_id,
            product_id=product2.id,
            customization_data={"text_2": "Product 2 text"},
            is_active=True
        )
        db_session.add_all([session1, session2])
        db_session.commit()

        # Act
        response = client.get(f"/api/v1/sessions/{session_id}")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should return a list of sessions
        assert isinstance(data, list)
        assert len(data) == 2

        # Verify both sessions are returned
        session_ids = {s["product_id"] for s in data}
        assert str(sample_product.id) in session_ids
        assert str(product2.id) in session_ids

        # Verify template versions
        for session_data in data:
            if session_data["product_id"] == str(sample_product.id):
                assert session_data["template_version"] == sample_template.version
                assert session_data["customization_data"]["text_1"] == "Product 1 text"
            else:
                assert session_data["template_version"] == template2.version
                assert session_data["customization_data"]["text_2"] == "Product 2 text"

    def test_get_session_with_empty_customization_data(
        self, client, db_session, sample_product, sample_template
    ):
        """
        GIVEN a session with empty customization data
        WHEN the GET /sessions/{sessionId} endpoint is called
        THEN the session should be returned with empty customization data
        """
        # Arrange
        session_id = "empty-data-session"

        db_customization_session = CustomizationSession(
            session_id=session_id,
            product_id=sample_product.id,
            customization_data={},
            is_active=True
        )
        db_session.add(db_customization_session)
        db_session.commit()

        # Act
        response = client.get(f"/api/v1/sessions/{session_id}")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["customization_data"] == {}
        assert data["template_version"] == sample_template.version

    def test_get_session_validates_session_id_format(self, client):
        """
        GIVEN a session ID with special characters
        WHEN the GET /sessions/{sessionId} endpoint is called
        THEN the endpoint should handle it properly (URL encoding)
        """
        # Arrange
        # Test with URL-safe session ID
        session_id = "session-with-dashes_and_underscores123"

        # Act
        response = client.get(f"/api/v1/sessions/{session_id}")

        # Assert
        # Should return 404 (not found) rather than a validation error
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_session_returns_most_recent_template_version(
        self, client, db_session, sample_product
    ):
        """
        GIVEN a product with multiple template versions and a session
        WHEN the GET /sessions/{sessionId} endpoint is called
        THEN the response should include the default/current template version
        """
        # Arrange
        session_id = "template-version-session"

        # Create multiple templates for the product
        template1 = Template(
            product_id=sample_product.id,
            version=1,
            definition={"zones": {"text_1": {"type": "text"}}},
            is_default=False
        )
        template2 = Template(
            product_id=sample_product.id,
            version=2,
            definition={"zones": {"text_2": {"type": "text"}}},
            is_default=True  # This is the current version
        )
        db_session.add_all([template1, template2])
        db_session.commit()

        # Create customization session
        db_customization_session = CustomizationSession(
            session_id=session_id,
            product_id=sample_product.id,
            customization_data={"text_1": "Some text"},
            is_active=True
        )
        db_session.add(db_customization_session)
        db_session.commit()

        # Act
        response = client.get(f"/api/v1/sessions/{session_id}")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should return the default template version (version 2)
        assert data["template_version"] == 2

    def test_get_session_handles_product_without_template(
        self, client, db_session
    ):
        """
        GIVEN a session for a product that has no template
        WHEN the GET /sessions/{sessionId} endpoint is called
        THEN the response should handle it gracefully with null template version
        """
        # Arrange
        session_id = "no-template-session"

        # Create a product without template
        product = Product(
            name="Product Without Template",
            description="Test product",
            base_price=19.99,
            media={},
            is_active=True
        )
        db_session.add(product)
        db_session.commit()
        db_session.refresh(product)

        # Create customization session
        db_customization_session = CustomizationSession(
            session_id=session_id,
            product_id=product.id,
            customization_data={"test": "data"},
            is_active=True
        )
        db_session.add(db_customization_session)
        db_session.commit()

        # Act
        response = client.get(f"/api/v1/sessions/{session_id}")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["template_version"] is None
