"""
Integration tests for Template CRUD operations.
"""
import pytest
from uuid import uuid4
from sqlalchemy.orm import Session

from app.models.template import Template, CustomizationZone
from app.schemas.template import TemplateCreate, TemplateUpdate, CustomizationZoneCreate
from app.crud import template as crud_template


def test_create_template(db_session: Session, sample_product):
    """Test creating a new template."""
    # Arrange
    template_data = TemplateCreate(
        product_id=sample_product.id,
        version=1,
        definition={
            "zones": {
                "text_1": {"type": "text", "max_length": 50},
                "image_1": {"type": "image", "formats": ["png", "jpg"]}
            }
        },
        is_default=True,
        customization_zones=[
            CustomizationZoneCreate(
                key="text_1", 
                type="text", 
                config={"max_length": 50}, 
                order_index=0
            ),
            CustomizationZoneCreate(
                key="image_1", 
                type="image", 
                config={"formats": ["png", "jpg"]}, 
                order_index=1
            )
        ]
    )
    
    # Act
    created_template = crud_template.create_template(db=db_session, template_in=template_data)
    
    # Assert
    assert created_template.id is not None
    assert created_template.product_id == sample_product.id
    assert created_template.version == 1
    assert created_template.is_default is True
    assert len(created_template.customization_zones) == 2
    
    # Check zones were created correctly
    zone_keys = {zone.key for zone in created_template.customization_zones}
    assert "text_1" in zone_keys
    assert "image_1" in zone_keys
    
    # Check the template is set as default
    default_template = crud_template.get_default_template(db=db_session, product_id=sample_product.id)
    assert default_template is not None
    assert default_template.id == created_template.id


def test_create_template_duplicate_version(db_session: Session, sample_product):
    """Test creating a template with a duplicate version fails."""
    # Arrange - create first template
    template_data = TemplateCreate(
        product_id=sample_product.id,
        version=1,
        definition={"zones": {"text_1": {"type": "text"}}},
        is_default=True
    )
    crud_template.create_template(db=db_session, template_in=template_data)
    
    # Act & Assert - try to create another template with same version
    with pytest.raises(ValueError) as exc_info:
        crud_template.create_template(db=db_session, template_in=template_data)
    
    assert "already exists for this product" in str(exc_info.value)


def test_update_template(db_session: Session, sample_template):
    """Test updating a template."""
    # Arrange - get the template ID
    template_id = sample_template.id
    
    # First, create a second template to be the default
    second_template = crud_template.create_template(
        db=db_session,
        template_in=TemplateCreate(
            product_id=sample_template.product_id,
            version=2,
            is_default=True,
            definition={"zones": {"another_zone": {"type": "text"}}},
            customization_zones=[
                CustomizationZoneCreate(
                    key="another_zone",
                    type="text",
                    order_index=0
                )
            ]
        )
    )
    
    # Act - update the first template
    update_data = TemplateUpdate(
        version=3,  # Bump version
        is_default=False,  # This is okay now since we have another default
        definition={"zones": {"updated_zone": {"type": "text"}}},
    )
    
    # Get the template object first
    template = crud_template.get_template(db=db_session, template_id=template_id)
    updated_template = crud_template.update_template(
        db=db_session,
        template=template,
        template_in=update_data
    )
    
    # Assert
    assert updated_template.version == 3
    assert updated_template.is_default is False
    assert "updated_zone" in updated_template.definition["zones"]


def test_delete_template(db_session: Session, sample_template):
    """Test deleting a template."""
    # Arrange - create another template for the same product
    another_template = Template(
        product_id=sample_template.product_id,
        version=2,
        definition={"zones": {"another_zone": {"type": "text"}}},
        is_default=False
    )
    db_session.add(another_template)
    db_session.commit()
    
    # Act - delete the first template
    result = crud_template.delete_template(db=db_session, template_id=sample_template.id)
    
    # Assert
    assert result is True
    assert crud_template.get_template(db=db_session, template_id=sample_template.id) is None
    
    # The other template should still exist
    assert crud_template.get_template(db=db_session, template_id=another_template.id) is not None


def test_delete_default_template_switches_default(db_session: Session, sample_product):
    """Test that deleting the default template makes another one the default."""
    # Arrange - create two templates, one default and one not
    default_template = Template(
        product_id=sample_product.id,
        version=1,
        definition={"zones": {"zone1": {"type": "text"}}},
        is_default=True
    )
    non_default_template = Template(
        product_id=sample_product.id,
        version=2,
        definition={"zones": {"zone2": {"type": "text"}}},
        is_default=False
    )
    db_session.add_all([default_template, non_default_template])
    db_session.commit()
    
    # Act - delete the default template
    result = crud_template.delete_template(db=db_session, template_id=default_template.id)
    
    # Assert
    assert result is True
    
    # The non-default template should now be the default
    updated_template = crud_template.get_template(db=db_session, template_id=non_default_template.id)
    assert updated_template.is_default is True
    
    # The default template should be the only one returned
    default_template = crud_template.get_default_template(db=db_session, product_id=sample_product.id)
    assert default_template.id == non_default_template.id
