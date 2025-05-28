"""
Unit tests for Template Pydantic schemas.
"""
import pytest
from uuid import UUID, uuid4
from pydantic import ValidationError

from app.schemas.template import (
    CustomizationZoneBase,
    CustomizationZoneCreate,
    TemplateBase,
    TemplateCreate,
    TemplateUpdate
)


def test_customization_zone_base_validation():
    """Test validation for CustomizationZoneBase schema."""
    # Valid data
    zone = CustomizationZoneBase(
        key="text_field_1",
        type="text",
        config={"max_length": 50},
        order_index=0
    )
    assert zone.key == "text_field_1"
    assert zone.type == "text"
    assert zone.config == {"max_length": 50}
    assert zone.order_index == 0
    
    # Test required fields
    with pytest.raises(ValidationError) as exc_info:
        CustomizationZoneBase(key="", type="text", order_index=0)
    assert "String should have at least 1 character" in str(exc_info.value)


def test_template_base_validation():
    """Test validation for TemplateBase schema."""
    # Valid data
    template = TemplateBase(
        product_id=uuid4(),
        version=1,
        definition={
            "zones": {
                "text_1": {"type": "text", "max_length": 50},
                "image_1": {"type": "image", "formats": ["png", "jpg"]}
            }
        },
        is_default=True
    )
    assert template.version == 1
    assert template.is_default is True
    assert "text_1" in template.definition["zones"]
    
    # Test invalid definition
    with pytest.raises(ValidationError) as exc_info:
        TemplateBase(
            product_id=uuid4(),
            version=1,
            definition={"invalid": "data"},
            is_default=True
        )
    assert "Template definition must contain 'zones' field" in str(exc_info.value)
    
    # Test invalid zone type
    with pytest.raises(ValidationError) as exc_info:
        TemplateBase(
            product_id=uuid4(),
            version=1,
            definition={"zones": {"invalid": {"type": "invalid_type"}}},
            is_default=True
        )
    assert "Invalid zone type 'invalid_type'" in str(exc_info.value)


def test_template_create_validation():
    """Test validation for TemplateCreate schema."""
    # Valid data with customization zones
    template = TemplateCreate(
        product_id=uuid4(),
        version=1,
        definition={
            "zones": {
                "text_1": {"type": "text", "max_length": 50}
            }
        },
        is_default=True,
        customization_zones=[
            {"key": "text_1", "type": "text", "config": {"max_length": 50}, "order_index": 0}
        ]
    )
    assert len(template.customization_zones) == 1
    assert template.customization_zones[0].key == "text_1"
    
    # Test zone mismatch between definition and customization_zones
    with pytest.raises(ValidationError) as exc_info:
        TemplateCreate(
            product_id=uuid4(),
            version=1,
            definition={"zones": {"text_1": {"type": "text"}}},
            is_default=True,
            customization_zones=[
                {"key": "different_key", "type": "text", "order_index": 0}
            ]
        )
    assert "Missing customization zones for defined zones: text_1" in str(exc_info.value)


def test_template_update_validation():
    """Test validation for TemplateUpdate schema."""
    # Partial update with just is_default
    update = TemplateUpdate(is_default=True)
    assert update.is_default is True
    assert update.version is None  # version is optional and not set
    assert update.definition is None
    
    # Update with version and definition
    update = TemplateUpdate(
        version=2,
        definition={"zones": {"text_1": {"type": "text"}}},
        is_default=True
    )
    assert update.version == 2
    assert "text_1" in update.definition["zones"]
    assert update.is_default is True
    
    # Test invalid definition
    with pytest.raises(ValidationError) as exc_info:
        TemplateUpdate(definition={"invalid": "data"})
    assert "Template definition must contain 'zones' field" in str(exc_info.value)
