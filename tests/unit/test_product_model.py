"""
Unit tests for Product model.
"""
import pytest
from uuid import UUID
from decimal import Decimal

from app.models.product import Product


class TestProductModel:
    """
    Test suite for Product model.
    
    Following BDD pattern with descriptive test method names.
    """
    
    def test_product_init_creates_product_with_expected_attributes(self, db_session):
        """
        GIVEN a Product model
        WHEN a new Product is created
        THEN it should have the expected attributes with correct values
        """
        # Arrange
        product_data = {
            "name": "Test Product",
            "description": "A test product",
            "base_price": Decimal("19.99"),
            "media": {"images": ["test.jpg"]},
            "is_active": True
        }
        
        # Act
        product = Product(**product_data)
        db_session.add(product)
        db_session.commit()
        
        # Assert
        assert product.id is not None
        assert isinstance(product.id, UUID)
        assert product.name == "Test Product"
        assert product.description == "A test product"
        assert product.base_price == Decimal("19.99")
        assert product.media == {"images": ["test.jpg"]}
        assert product.is_active is True
        assert product.created_at is not None
        assert product.updated_at is not None
    
    def test_product_repr_returns_expected_string(self, db_session):
        """
        GIVEN a Product model instance
        WHEN __repr__ is called
        THEN it should return a string containing the product name
        """
        # Arrange
        product = Product(name="Test Product")
        
        # Act
        result = repr(product)
        
        # Assert
        assert "Test Product" in result
        assert "<Product" in result
    
    def test_product_relationships_cascade_on_delete(self, db_session):
        """
        GIVEN a Product with Templates
        WHEN the Product is deleted
        THEN all related Templates should be deleted (cascade)
        """
        # This test would need the Template model implementation
        # Will be implemented with the Template model tests
        pass
