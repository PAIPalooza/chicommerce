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
    Create a new template with proper versioning and default template handling.
    
    Args:
        db: Database session
        template_in: Template creation data
        
    Returns:
        Created Template object
        
    Raises:
        ValueError: If version already exists for the product
    """
    # Check if version already exists for this product
    existing = db.query(Template).filter(
        Template.product_id == template_in.product_id,
        Template.version == template_in.version
    ).first()
    
    if existing:
        raise ValueError(f"Version {template_in.version} already exists for this product")
    
    # If this is marked as default, unmark any existing default templates
    if template_in.is_default:
        db.query(Template).filter(
            Template.product_id == template_in.product_id,
            Template.is_default == True
        ).update({Template.is_default: False})
    # If no default exists for this product, make this the default
    elif not get_default_template(db, product_id=template_in.product_id):
        template_in.is_default = True
    
    # Get the next version number if not provided (should be handled by schema validation)
    if not template_in.version:
        latest_template = db.query(Template).filter(
            Template.product_id == template_in.product_id
        ).order_by(Template.version.desc()).first()
        
        template_in.version = latest_template.version + 1 if latest_template else 1
    
    # Create the template
    template_data = template_in.model_dump(exclude={"customization_zones"})
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
    Update a template with proper versioning and default template handling.
    
    Args:
        db: Database session
        template: Existing template object
        template_in: Template update data
        
    Returns:
        Updated Template object
        
    Raises:
        ValueError: If version conflicts or validation fails
    """
    update_data = template_in.model_dump(exclude_unset=True, exclude_none=True)
    
    # Check for version conflicts if version is being updated
    if 'version' in update_data and update_data['version'] != template.version:
        # Check if the new version already exists for this product
        existing = db.query(Template).filter(
            Template.product_id == template.product_id,
            Template.version == update_data['version'],
            Template.id != template.id  # Exclude current template
        ).first()
        
        if existing:
            raise ValueError(f"Version {update_data['version']} already exists for this product")
    
    # Handle default template changes
    if update_data.get('is_default') is True and not template.is_default:
        # Unmark any existing default templates
        db.query(Template).filter(
            Template.product_id == template.product_id,
            Template.is_default == True,
            Template.id != template.id  # Don't unmark ourselves
        ).update({Template.is_default: False})
    elif update_data.get('is_default') is False and template.is_default:
        # If unsetting default, ensure there's at least one default remaining
        other_defaults = db.query(Template).filter(
            Template.product_id == template.product_id,
            Template.is_default == True,
            Template.id != template.id
        ).count()
        
        if other_defaults == 0:
            raise ValueError("At least one template must be marked as default")
    
    # Update the template fields
    for field, value in update_data.items():
        setattr(template, field, value)
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return template


def delete_template(db: Session, template_id: UUID) -> bool:
    """
    Delete a template with proper default template handling.
    
    Args:
        db: Database session
        template_id: UUID of the template to delete
        
    Returns:
        True if deleted, False if not found
        
    Raises:
        ValueError: If trying to delete the only template for a product
    """
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        return False
    
    # Check if this is the last template for the product
    other_templates_count = db.query(Template).filter(
        Template.product_id == template.product_id,
        Template.id != template.id
    ).count()
    
    if other_templates_count == 0:
        raise ValueError("Cannot delete the only template for a product")
    
    # If this is the default template, make another template the default
    if template.is_default:
        # Find the first non-deleted template for this product
        new_default = db.query(Template).filter(
            Template.product_id == template.product_id,
            Template.id != template.id
        ).first()
        
        if new_default:
            new_default.is_default = True
            db.add(new_default)
    
    db.delete(template)
    db.commit()
    return True
