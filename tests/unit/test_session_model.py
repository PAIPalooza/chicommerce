"""
Unit tests for CustomizationSession model.

Following BDD pattern with describe/it syntax using pytest.
"""
import pytest
from uuid import UUID
from datetime import datetime

from app.models.cart import CustomizationSession
from app.models.product import Product
from app.models.template import Template


class TestCustomizationSessionModel:
    """Test suite for CustomizationSession model."""

    def test_session_init_creates_session_with_expected_attributes(self, db_session, sample_product, sample_template):
        """
        GIVEN a CustomizationSession model
        WHEN a new CustomizationSession is created with product_id and template_id
        THEN it should have the expected attributes with correct values
        """
        # Arrange
        session_data = {
            "product_id": sample_product.id,
            "template_id": sample_template.id,
            "session_key": "test-session-key-123",
            "options": {}
        }

        # Act
        session = CustomizationSession(**session_data)
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        # Assert
        assert session.id is not None
        assert isinstance(session.id, UUID)
        assert session.product_id == sample_product.id
        assert session.template_id == sample_template.id
        assert session.session_key == "test-session-key-123"
        assert session.options == {}
        assert session.is_active is True
        assert session.created_at is not None
        assert session.updated_at is not None
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.updated_at, datetime)

    def test_session_key_is_unique_and_indexed(self, db_session, sample_product, sample_template):
        """
        GIVEN two CustomizationSessions
        WHEN they have the same session_key
        THEN it should raise an integrity error (unique constraint)
        """
        # Arrange
        session1 = CustomizationSession(
            product_id=sample_product.id,
            template_id=sample_template.id,
            session_key="unique-key-123",
            options={}
        )
        db_session.add(session1)
        db_session.commit()

        session2 = CustomizationSession(
            product_id=sample_product.id,
            template_id=sample_template.id,
            session_key="unique-key-123",
            options={}
        )

        # Act & Assert
        db_session.add(session2)
        with pytest.raises(Exception):  # SQLAlchemy IntegrityError
            db_session.commit()
        db_session.rollback()

    def test_session_defaults_to_empty_options(self, db_session, sample_product, sample_template):
        """
        GIVEN a CustomizationSession created without options
        WHEN the session is saved
        THEN it should have an empty dict for options
        """
        # Arrange & Act
        session = CustomizationSession(
            product_id=sample_product.id,
            template_id=sample_template.id,
            session_key="test-key"
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        # Assert
        assert session.options == {}

    def test_session_defaults_to_active(self, db_session, sample_product, sample_template):
        """
        GIVEN a CustomizationSession created without is_active
        WHEN the session is saved
        THEN it should default to is_active=True
        """
        # Arrange & Act
        session = CustomizationSession(
            product_id=sample_product.id,
            template_id=sample_template.id,
            session_key="test-key",
            options={}
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        # Assert
        assert session.is_active is True

    def test_session_product_relationship(self, db_session, sample_product, sample_template):
        """
        GIVEN a CustomizationSession linked to a Product
        WHEN accessing the product relationship
        THEN it should return the correct Product instance
        """
        # Arrange
        session = CustomizationSession(
            product_id=sample_product.id,
            template_id=sample_template.id,
            session_key="test-key",
            options={}
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        # Act
        product = session.product

        # Assert
        assert product is not None
        assert product.id == sample_product.id
        assert product.name == sample_product.name

    def test_session_template_relationship(self, db_session, sample_product, sample_template):
        """
        GIVEN a CustomizationSession linked to a Template
        WHEN accessing the template relationship
        THEN it should return the correct Template instance
        """
        # Arrange
        session = CustomizationSession(
            product_id=sample_product.id,
            template_id=sample_template.id,
            session_key="test-key",
            options={}
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        # Act
        template = session.template

        # Assert
        assert template is not None
        assert template.id == sample_template.id
        assert template.product_id == sample_product.id

    def test_session_repr_returns_expected_string(self, db_session, sample_product, sample_template):
        """
        GIVEN a CustomizationSession instance
        WHEN __repr__ is called
        THEN it should return a string containing session and product info
        """
        # Arrange
        session = CustomizationSession(
            product_id=sample_product.id,
            template_id=sample_template.id,
            session_key="test-key",
            options={}
        )
        db_session.add(session)
        db_session.commit()

        # Act
        result = repr(session)

        # Assert
        assert "<CustomizationSession" in result
        assert str(session.id) in result

    def test_session_cascade_delete_with_product(self, db_session, sample_product, sample_template):
        """
        GIVEN a CustomizationSession linked to a Product
        WHEN the Product is deleted
        THEN the CustomizationSession should also be deleted (cascade)
        """
        # Arrange
        session = CustomizationSession(
            product_id=sample_product.id,
            template_id=sample_template.id,
            session_key="test-key",
            options={}
        )
        db_session.add(session)
        db_session.commit()
        session_id = session.id

        # Act
        db_session.delete(sample_product)
        db_session.commit()

        # Assert
        deleted_session = db_session.query(CustomizationSession).filter_by(id=session_id).first()
        assert deleted_session is None
