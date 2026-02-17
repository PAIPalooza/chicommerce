"""
Unit tests for CustomizationSession Pydantic schemas.

Following BDD pattern with describe/it syntax using pytest.
"""
import pytest
from uuid import uuid4
from pydantic import ValidationError

from app.schemas.session import SessionCreate, SessionResponse


class TestSessionCreateSchema:
    """Test suite for SessionCreate schema validation."""

    def test_valid_session_create_with_required_fields(self):
        """
        GIVEN valid product_id and template_id
        WHEN creating a SessionCreate schema
        THEN it should validate successfully
        """
        # Arrange
        product_id = uuid4()
        template_id = uuid4()

        # Act
        session_data = SessionCreate(
            product_id=product_id,
            template_id=template_id
        )

        # Assert
        assert session_data.product_id == product_id
        assert session_data.template_id == template_id

    def test_session_create_validates_uuid_format(self):
        """
        GIVEN invalid UUID strings
        WHEN creating a SessionCreate schema
        THEN it should raise ValidationError
        """
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            SessionCreate(
                product_id="not-a-uuid",
                template_id=uuid4()
            )

        # Check that the error is related to UUID validation
        errors = exc_info.value.errors()
        assert any("uuid" in str(error).lower() for error in errors)

    def test_session_create_requires_product_id(self):
        """
        GIVEN SessionCreate data without product_id
        WHEN validating the schema
        THEN it should raise ValidationError
        """
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            SessionCreate(template_id=uuid4())

        errors = exc_info.value.errors()
        assert any(error['loc'] == ('product_id',) for error in errors)

    def test_session_create_requires_template_id(self):
        """
        GIVEN SessionCreate data without template_id
        WHEN validating the schema
        THEN it should raise ValidationError
        """
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            SessionCreate(product_id=uuid4())

        errors = exc_info.value.errors()
        assert any(error['loc'] == ('template_id',) for error in errors)


class TestSessionResponseSchema:
    """Test suite for SessionResponse schema validation."""

    def test_valid_session_response_with_all_fields(self):
        """
        GIVEN valid session data
        WHEN creating a SessionResponse schema
        THEN it should validate successfully with all fields
        """
        # Arrange
        session_id = uuid4()
        product_id = uuid4()
        template_id = uuid4()
        session_key = "secure-session-key-123"

        # Act
        response = SessionResponse(
            session_id=session_id,
            session_key=session_key,
            product_id=product_id,
            template_id=template_id,
            options={}
        )

        # Assert
        assert response.session_id == session_id
        assert response.session_key == session_key
        assert response.product_id == product_id
        assert response.template_id == template_id
        assert response.options == {}

    def test_session_response_validates_session_id_uuid(self):
        """
        GIVEN invalid session_id format
        WHEN creating a SessionResponse schema
        THEN it should raise ValidationError
        """
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            SessionResponse(
                session_id="not-a-uuid",
                session_key="key",
                product_id=uuid4(),
                template_id=uuid4(),
                options={}
            )

        errors = exc_info.value.errors()
        assert any("uuid" in str(error).lower() for error in errors)

    def test_session_response_requires_session_key(self):
        """
        GIVEN SessionResponse data without session_key
        WHEN validating the schema
        THEN it should raise ValidationError
        """
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            SessionResponse(
                session_id=uuid4(),
                product_id=uuid4(),
                template_id=uuid4(),
                options={}
            )

        errors = exc_info.value.errors()
        assert any(error['loc'] == ('session_key',) for error in errors)

    def test_session_response_defaults_empty_options(self):
        """
        GIVEN SessionResponse data without options
        WHEN creating the schema
        THEN it should default to an empty dict
        """
        # Arrange & Act
        response = SessionResponse(
            session_id=uuid4(),
            session_key="key",
            product_id=uuid4(),
            template_id=uuid4()
        )

        # Assert
        assert response.options == {}

    def test_session_response_accepts_populated_options(self):
        """
        GIVEN SessionResponse with customization options
        WHEN creating the schema
        THEN it should preserve the options data
        """
        # Arrange
        options_data = {
            "color": "red",
            "text": "Custom Text",
            "size": "large"
        }

        # Act
        response = SessionResponse(
            session_id=uuid4(),
            session_key="key",
            product_id=uuid4(),
            template_id=uuid4(),
            options=options_data
        )

        # Assert
        assert response.options == options_data
        assert response.options["color"] == "red"
        assert response.options["text"] == "Custom Text"
        assert response.options["size"] == "large"
