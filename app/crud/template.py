"""
CRUD operations for Template model.
"""
from typing import List, Optional, Dict, Any, Union
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import select, update

from app.models.template import Template, CustomizationZone
from app.schemas.template import TemplateCreate, TemplateUpdate


def get_template(db: Session, template_id: UUID) -> Optional[Template]:
    """
    Get a template by ID.
    
    Args:
        db: Database session
        template_id: UUID of the template
        
    Returns:
        Template object or None if not found
    """
    return db.query(Template).filter(Template.id == template_id).first()


def get_templates_by_product(db: Session, product_id: UUID) -> List[Template]:
    """
    Get all templates for a product.
    
    Args:
        db: Database session
        product_id: UUID of the product
        
    Returns:
        List of Template objects
    """
    return db.query(Template).filter(Template.product_id == product_id).order_by(Template.version.desc()).all()


def get_default_template(db: Session, product_id: UUID) -> Optional[Template]:
    """
    Get the default template for a product.
    
    Args:
        db: Database session
        product_id: UUID of the product
        
    Returns:
        Template object or None if not found
    """
    return db.query(Template).filter(
        Template.product_id == product_id,
        Template.is_default == True
    ).first()


def create_template(db: Session, template_in: TemplateCreate) -> Template:
    """
    Create a new template.
    
    Args:
        db: Database session
        template_in: Template creation data
        
    Returns:
        Created Template object
    """
    # If this is marked as default, unmark any existing default templates
    if template_in.is_default:
        db.query(Template).filter(
            Template.product_id == template_in.product_id,
            Template.is_default == True
        ).update({Template.is_default: False})
    
    # Create the template
    template_data = template_in.dict(exclude={"customization_zones"})
    template = Template(**template_data)
    db.add(template)
    db.flush()  # Flush to get template ID without committing
    
    # Create customization zones if provided
    if template_in.customization_zones:
        for i, zone_data in enumerate(template_in.customization_zones):
            zone = CustomizationZone(
                template_id=template.id,
                key=zone_data.key,
                type=zone_data.type,
                config=zone_data.config,
                order_index=zone_data.order_index if zone_data.order_index is not None else i
            )
            db.add(zone)
    
    db.commit()
    db.refresh(template)
    return template


def update_template(
    db: Session, 
    template: Template, 
    template_in: TemplateUpdate
) -> Template:
    """
    Update a template.
    
    Args:
        db: Database session
        template: Existing template object
        template_in: Template update data
        
    Returns:
        Updated Template object
    """
    update_data = template_in.dict(exclude_unset=True)
    
    # If changing to default, unmark any existing default templates
    if update_data.get("is_default", False) and not template.is_default:
        db.query(Template).filter(
            Template.product_id == template.product_id,
            Template.is_default == True
        ).update({Template.is_default: False})
    
    for field, value in update_data.items():
        setattr(template, field, value)
        
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def delete_template(db: Session, template_id: UUID) -> bool:
    """
    Delete a template.
    
    Args:
        db: Database session
        template_id: UUID of the template to delete
        
    Returns:
        True if deleted, False if not found
    """
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        return False
    
    db.delete(template)
    db.commit()
    return True
