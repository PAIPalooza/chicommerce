"""
Unit tests for Template model.
"""
import pytest
from uuid import UUID
from decimal import Decimal

from app.models.product import Product
from app.models.template import Template, CustomizationZone


class TestTemplateModel:
    """
    Test suite for Template model.
    
    Following BDD pattern with descriptive test method names.
    """
    
    def test_template_init_creates_template_with_expected_attributes(self, db_session):
        """
        GIVEN a Template model
        WHEN a new Template is created
        THEN it should have the expected attributes with correct values
        """
        # Arrange
        product = Product(
            name="Test Product",
            description="A test product",
            base_price=Decimal("19.99"),
            is_active=True
        )
        db_session.add(product)
        db_session.flush()
        
        template_data = {
            "product_id": product.id,
            "version": 1,
            "definition": {"zones": {"text_front": {"type": "text"}}},
            "is_default": True
        }
        
        # Act
        template = Template(**template_data)
        db_session.add(template)
        db_session.commit()
        
        # Assert
        assert template.id is not None
        assert isinstance(template.id, UUID)
        assert template.product_id == product.id
        assert template.version == 1
        assert template.definition == {"zones": {"text_front": {"type": "text"}}}
        assert template.is_default is True
        assert template.created_at is not None
        assert template.updated_at is not None
    
    def test_template_repr_returns_expected_string(self, db_session):
        """
        GIVEN a Template model instance
        WHEN __repr__ is called
        THEN it should return a string containing the product_id and version
        """
        # Arrange
        product = Product(name="Test Product", base_price=Decimal("19.99"))
        db_session.add(product)
        db_session.flush()
        
        template = Template(
            product_id=product.id,
            version=1,
            definition={},
            is_default=True
        )
        
        # Act
        result = repr(template)
        
        # Assert
        assert str(product.id) in result
        assert "v1" in result
        assert "<Template" in result
    
    def test_customization_zone_init_creates_zone_with_expected_attributes(self, db_session):
        """
        GIVEN a CustomizationZone model
        WHEN a new CustomizationZone is created
        THEN it should have the expected attributes with correct values
        """
        # Arrange
        product = Product(name="Test Product", base_price=Decimal("19.99"))
        db_session.add(product)
        db_session.flush()
        
        template = Template(
            product_id=product.id,
            version=1,
            definition={},
            is_default=True
        )
        db_session.add(template)
        db_session.flush()
        
        zone_data = {
            "template_id": template.id,
            "key": "text_front",
            "type": "text",
            "config": {"max_length": 50},
            "order_index": 0
        }
        
        # Act
        zone = CustomizationZone(**zone_data)
        db_session.add(zone)
        db_session.commit()
        
        # Assert
        assert zone.id is not None
        assert isinstance(zone.id, UUID)
        assert zone.template_id == template.id
        assert zone.key == "text_front"
        assert zone.type == "text"
        assert zone.config == {"max_length": 50}
        assert zone.order_index == 0
    
    def test_template_relationships_cascade_on_delete(self, db_session):
        """
        GIVEN a Template with CustomizationZones
        WHEN the Template is deleted
        THEN all related CustomizationZones should be deleted (cascade)
        """
        # Arrange
        product = Product(name="Test Product", base_price=Decimal("19.99"))
        db_session.add(product)
        db_session.flush()
        
        template = Template(
            product_id=product.id,
            version=1,
            definition={},
            is_default=True
        )
        db_session.add(template)
        db_session.flush()
        
        zone = CustomizationZone(
            template_id=template.id,
            key="text_front",
            type="text",
            config={"max_length": 50},
            order_index=0
        )
        db_session.add(zone)
        db_session.commit()
        
        zone_id = zone.id
        
        # Act
        db_session.delete(template)
        db_session.commit()
        
        # Assert
        deleted_zone = db_session.query(CustomizationZone).filter(CustomizationZone.id == zone_id).first()
        assert deleted_zone is None
    
    def test_product_relationships_cascade_on_delete(self, db_session):
        """
        GIVEN a Product with Templates
        WHEN the Product is deleted
        THEN all related Templates should be deleted (cascade)
        """
        # Arrange
        product = Product(name="Test Product", base_price=Decimal("19.99"))
        db_session.add(product)
        db_session.flush()
        
        template = Template(
            product_id=product.id,
            version=1,
            definition={},
            is_default=True
        )
        db_session.add(template)
        db_session.commit()
        
        template_id = template.id
        
        # Act
        db_session.delete(product)
        db_session.commit()
        
        # Assert
        deleted_template = db_session.query(Template).filter(Template.id == template_id).first()
        assert deleted_template is None
