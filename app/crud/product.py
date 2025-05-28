"""
CRUD operations for Product model.
"""
from typing import List, Optional, Dict, Any, Union
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.product import Product
from app.models.template import Template
from app.schemas.product import ProductCreate, ProductUpdate


def get_product(db: Session, product_id: UUID) -> Optional[Product]:
    """
    Get a product by ID.
    
    Args:
        db: Database session
        product_id: UUID of the product
        
    Returns:
        Product object or None if not found
    """
    return db.query(Product).filter(Product.id == product_id).first()


def get_product_with_default_template(db: Session, product_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Get a product by ID with its default template.
    
    Args:
        db: Database session
        product_id: UUID of the product
        
    Returns:
        Dictionary with product and default_template or None if not found
    """
    # SQLAlchemy 2.0 style query
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        return None
    
    # Get default template if it exists
    default_template = db.query(Template).filter(
        Template.product_id == product_id,
        Template.is_default == True
    ).first()
    
    # Convert product to dict for response
    product_dict = {c.name: getattr(product, c.name) for c in product.__table__.columns}
    
    # Add default template if it exists
    if default_template:
        template_dict = {c.name: getattr(default_template, c.name) for c in default_template.__table__.columns}
        product_dict["default_template"] = template_dict
    else:
        product_dict["default_template"] = None
        
    return product_dict


def get_products(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    active_only: bool = True
) -> List[Product]:
    """
    Get multiple products with pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        active_only: If True, returns only active products
        
    Returns:
        List of Product objects
    """
    query = db.query(Product)
    
    if active_only:
        query = query.filter(Product.is_active == True)
        
    return query.order_by(Product.name).offset(skip).limit(limit).all()


def create_product(db: Session, product_in: ProductCreate) -> Product:
    """
    Create a new product.
    
    Args:
        db: Database session
        product_in: Product creation data
        
    Returns:
        Created Product object
    """
    product = Product(
        name=product_in.name,
        description=product_in.description,
        base_price=product_in.base_price,
        media=product_in.media,
        is_active=product_in.is_active
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(
    db: Session, 
    product: Product, 
    product_in: ProductUpdate
) -> Product:
    """
    Update a product.
    
    Args:
        db: Database session
        product: Existing product object
        product_in: Product update data
        
    Returns:
        Updated Product object
    """
    update_data = product_in.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(product, field, value)
        
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: UUID) -> bool:
    """
    Delete a product and handle related entities.
    
    Args:
        db: Database session
        product_id: UUID of the product to delete
        
    Returns:
        True if deleted, False if not found
        
    Raises:
        ValueError: If there are active cart items that prevent deletion
    """
    from app.models.cart import CartItem, CustomizationSession
    
    # Start a transaction
    try:
        # Check if product exists
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return False
            
        # Check for active cart items
        cart_items_count = db.query(CartItem).filter(
            CartItem.product_id == product_id
        ).count()
        
        if cart_items_count > 0:
            # Raise an error if there are cart items
            raise ValueError(
                f"Cannot delete product with {cart_items_count} cart items. "
                "Please remove all cart items before deleting the product."
            )
        
        # Delete all customization sessions for this product
        # This is necessary because of the foreign key constraint
        db.query(CustomizationSession).filter(
            CustomizationSession.product_id == product_id
        ).delete(synchronize_session=False)
        
        # Delete the product (this will cascade to templates and option_sets)
        db.delete(product)
        db.commit()
        return True
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Failed to delete product: {str(e)}")
