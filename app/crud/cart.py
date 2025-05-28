"""CRUD operations for cart functionality."""
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models.cart import Cart, CartItem, CustomizationSession
from app.schemas.cart import (
    CartCreate, CartUpdate, CartItemCreate, CartItemUpdate,
    CustomizationSessionCreate, CustomizationSessionUpdate
)


def get_cart(db: Session, cart_id: UUID) -> Optional[Cart]:
    """Retrieve a cart by its ID."""
    return db.query(Cart).filter(Cart.id == cart_id).first()


def get_cart_by_session_id(db: Session, session_id: str) -> Optional[Cart]:
    """Retrieve a cart by session ID."""
    return (
        db.query(Cart)
        .options(
            joinedload(Cart.items)
            .joinedload(CartItem.product)
        )
        .filter(Cart.session_id == session_id)
        .first()
    )


def get_user_cart(db: Session, user_id: UUID) -> Optional[Cart]:
    """Retrieve a user's cart by user ID."""
    return (
        db.query(Cart)
        .options(joinedload(Cart.items).joinedload(CartItem.product))
        .filter(Cart.user_id == user_id)
        .first()
    )


def create_cart(db: Session, cart_in: CartCreate) -> Cart:
    """Create a new cart."""
    db_cart = Cart(**cart_in.dict())
    db.add(db_cart)
    db.commit()
    db.refresh(db_cart)
    return db_cart


def update_cart(db: Session, db_cart: Cart, cart_in: CartUpdate) -> Cart:
    """Update an existing cart."""
    update_data = cart_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_cart, field, value)
    db.commit()
    db.refresh(db_cart)
    return db_cart


def delete_cart(db: Session, cart_id: UUID) -> bool:
    """Delete a cart by ID."""
    db_cart = get_cart(db, cart_id)
    if not db_cart:
        return False
    db.delete(db_cart)
    db.commit()
    return True


def get_cart_item(db: Session, item_id: UUID) -> Optional[CartItem]:
    """Retrieve a cart item by ID."""
    return db.query(CartItem).filter(CartItem.id == item_id).first()


from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB

def add_item_to_cart(db: Session, cart_id: UUID, item_in: CartItemCreate) -> CartItem:
    """Add an item to a cart."""
    # First, find all items for this cart and product
    items = (
        db.query(CartItem)
        .filter(
            CartItem.cart_id == cart_id,
            CartItem.product_id == item_in.product_id
        )
        .all()
    )
    
    # Manually check for matching customization data
    existing_item = None
    for item in items:
        if item.customization_data == (item_in.customization_data or {}):
            existing_item = item
            break
    
    if existing_item:
        # If item exists, update the quantity
        existing_item.quantity += item_in.quantity
        db.commit()
        db.refresh(existing_item)
        return existing_item
    else:
        # Otherwise, create a new cart item
        db_item = CartItem(
            cart_id=cart_id,
            product_id=item_in.product_id,
            quantity=item_in.quantity,
            unit_price=item_in.unit_price,
            customization_data=item_in.customization_data or {}
        )
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item


def update_cart_item(
    db: Session, 
    db_item: CartItem, 
    item_in: CartItemUpdate
) -> CartItem:
    """Update a cart item."""
    update_data = item_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)
    db.commit()
    db.refresh(db_item)
    return db_item


def remove_item_from_cart(db: Session, item_id: UUID) -> bool:
    """Remove an item from a cart."""
    db_item = get_cart_item(db, item_id)
    if not db_item:
        return False
    db.delete(db_item)
    db.commit()
    return True


def clear_cart(db: Session, cart_id: UUID) -> None:
    """Remove all items from a cart."""
    db.query(CartItem).filter(CartItem.cart_id == cart_id).delete()
    db.commit()


def get_customization_session(
    db: Session, 
    session_id: str, 
    product_id: Optional[UUID] = None
) -> Optional[CustomizationSession]:
    """Retrieve a customization session by ID and optionally filter by product ID."""
    query = db.query(CustomizationSession).filter(
        CustomizationSession.session_id == session_id,
        CustomizationSession.is_active == True
    )
    
    if product_id:
        query = query.filter(CustomizationSession.product_id == product_id)
    
    return query.first()


def create_customization_session(
    db: Session, 
    session_in: CustomizationSessionCreate
) -> CustomizationSession:
    """Create a new customization session."""
    # Deactivate any existing sessions for this product and session ID
    db.query(CustomizationSession).filter(
        CustomizationSession.session_id == session_in.session_id,
        CustomizationSession.product_id == session_in.product_id
    ).update({"is_active": False})
    
    # Create new active session
    db_session = CustomizationSession(**session_in.dict())
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def update_customization_session(
    db: Session, 
    db_session: CustomizationSession, 
    session_in: CustomizationSessionUpdate
) -> CustomizationSession:
    """Update a customization session."""
    update_data = session_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_session, field, value)
    db.commit()
    db.refresh(db_session)
    return db_session


def delete_customization_session(db: Session, session_id: UUID) -> bool:
    """Delete a customization session."""
    db_session = (
        db.query(CustomizationSession)
        .filter(CustomizationSession.id == session_id)
        .first()
    )
    if not db_session:
        return False
    db.delete(db_session)
    db.commit()
    return True
