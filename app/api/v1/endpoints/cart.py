"""API endpoints for cart functionality."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app.api import deps
from app.core.config import settings
from app.crud import cart as crud_cart
from app.schemas.cart import (
    CartResponse, CartItemCreate, CartItemUpdate,
    CustomizationSessionCreate, CustomizationSessionUpdate, CustomizationSessionInDB
)

router = APIRouter()

# API Key for admin operations
ADMIN_API_KEY = settings.ADMIN_API_KEY
api_key_header = APIKeyHeader(name="X-API-Key")

def get_admin_key(api_key: str = Depends(api_key_header)) -> str:
    """Validate admin API key."""
    if api_key != ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return api_key

def get_or_create_cart(
    request: Request, 
    db: Session = Depends(deps.get_db)
):
    """Get existing cart or create a new one based on session."""
    session_id = request.cookies.get("session_id")
    if not session_id:
        # In a real app, you'd generate a secure session ID
        session_id = str(hash(request.client.host + str(request.url)))
    
    db_cart = crud_cart.get_cart_by_session_id(db, session_id=session_id)
    if not db_cart:
        # Create a new cart
        db_cart = crud_cart.create_cart(
            db, 
            cart_in=crud_cart.CartCreate(session_id=session_id)
        )
    
    return db_cart, session_id

@router.get("/cart", response_model=CartResponse)
async def get_cart(
    request: Request,
    db: Session = Depends(deps.get_db),
):
    """Retrieve the current user's cart."""
    db_cart, _ = get_or_create_cart(request, db)
    return format_cart_response(db_cart)

@router.post("/cart/items", response_model=CartResponse, status_code=status.HTTP_201_CREATED)
async def add_item_to_cart(
    item_in: CartItemCreate,
    request: Request,
    response: Response,
    db: Session = Depends(deps.get_db),
):
    """Add an item to the cart."""
    try:
        db_cart, session_id = get_or_create_cart(request, db)
        
        # Add item to cart
        try:
            crud_cart.add_item_to_cart(
                db, 
                cart_id=db_cart.id,
                item_in=item_in
            )
        except Exception as e:
            db.rollback()
            print(f"Error adding item to cart: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add item to cart: {str(e)}"
            )
        
        # Refresh cart to get updated data
        db_cart = crud_cart.get_cart_by_session_id(db, session_id=session_id)
        if not db_cart:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve updated cart"
            )
        
        # Format response to ensure it matches the schema
        try:
            response_data = format_cart_response(db_cart)
        except Exception as e:
            print(f"Error formatting cart response: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to format cart response: {str(e)}"
            )
        
        # Set session cookie if not already set
        if not request.cookies.get("session_id"):
            response.set_cookie(
                key="session_id",
                value=session_id,
                httponly=True,
                max_age=30 * 24 * 60 * 60,  # 30 days
                samesite="lax"
            )
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in add_item_to_cart: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.put("/cart/items/{item_id}", response_model=CartResponse)
async def update_cart_item(
    item_id: UUID,
    item_in: CartItemUpdate,
    request: Request,
    db: Session = Depends(deps.get_db),
):
    """Update an item in the cart."""
    db_cart, _ = get_or_create_cart(request, db)
    
    # Find the item in the cart
    db_item = next((item for item in db_cart.items if str(item.id) == str(item_id)), None)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found in cart"
        )
    
    # Update the item
    crud_cart.update_cart_item(
        db,
        db_item=db_item,
        item_in=item_in
    )
    
    # Refresh cart to get updated data
    db.refresh(db_cart)
    return format_cart_response(db_cart)

@router.delete("/cart/items/{item_id}", response_model=CartResponse)
async def remove_item_from_cart(
    item_id: UUID,
    request: Request,
    db: Session = Depends(deps.get_db),
):
    """Remove an item from the cart."""
    db_cart, _ = get_or_create_cart(request, db)
    
    # Find the item in the cart
    db_item = next((item for item in db_cart.items if str(item.id) == str(item_id)), None)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found in cart"
        )
    
    # Remove the item
    crud_cart.remove_item_from_cart(db, item_id=item_id)
    
    # Refresh cart to get updated data
    db.refresh(db_cart)
    return format_cart_response(db_cart)

@router.delete("/cart", response_model=CartResponse)
async def clear_cart(
    request: Request,
    db: Session = Depends(deps.get_db),
):
    """Clear all items from the cart."""
    db_cart, _ = get_or_create_cart(request, db)
    crud_cart.clear_cart(db, cart_id=db_cart.id)
    db.refresh(db_cart)
    return format_cart_response(db_cart)

# Customization Session Endpoints

@router.post("/customization-sessions", response_model=CustomizationSessionInDB)
async def create_customization_session(
    session_in: CustomizationSessionCreate,
    request: Request,
    db: Session = Depends(deps.get_db),
):
    """Create or update a customization session for a product."""
    db_session = crud_cart.create_customization_session(
        db,
        session_in=session_in
    )
    return db_session

@router.get("/customization-sessions/{product_id}", response_model=CustomizationSessionInDB)
async def get_customization_session(
    product_id: UUID,
    request: Request,
    db: Session = Depends(deps.get_db),
):
    """Get the current customization session for a product."""
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active session found"
        )
    
    db_session = crud_cart.get_customization_session(
        db,
        session_id=session_id,
        product_id=product_id
    )
    
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No customization session found for this product"
        )
    
    return db_session

@router.put("/customization-sessions/{product_id}", response_model=CustomizationSessionInDB)
async def update_customization_session(
    product_id: UUID,
    session_in: CustomizationSessionUpdate,
    request: Request,
    db: Session = Depends(deps.get_db),
):
    """Update a customization session."""
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active session found"
        )
    
    db_session = crud_cart.get_customization_session(
        db,
        session_id=session_id,
        product_id=product_id
    )
    
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No customization session found for this product"
        )
    
    updated_session = crud_cart.update_customization_session(
        db,
        db_session=db_session,
        session_in=session_in
    )
    
    return updated_session

def format_cart_response(db_cart) -> CartResponse:
    """Format cart data for the response."""
    from app.schemas.cart import CartItemWithProduct
    from app.schemas.product import ProductBase
    
    # Convert CartItem objects to CartItemWithProduct
    items_with_products = []
    for item in db_cart.items:
        # Convert Product model to ProductBase schema
        product_data = None
        if item.product:
            product_data = ProductBase(
                id=item.product.id,
                name=item.product.name,
                description=item.product.description,
                base_price=float(item.product.base_price),  # Ensure it's a float
                media=item.product.media or {},
                is_active=item.product.is_active,
                created_at=item.product.created_at,
                updated_at=item.product.updated_at
            )
        
        item_dict = {
            'id': item.id,
            'cart_id': item.cart_id,
            'product_id': item.product_id,
            'quantity': item.quantity,
            'unit_price': float(item.unit_price),  # Ensure it's a float
            'customization_data': item.customization_data or {},
            'created_at': item.created_at,
            'updated_at': item.updated_at,
            'product': product_data
        }
        items_with_products.append(CartItemWithProduct(**item_dict))
    
    subtotal = sum(item.quantity * item.unit_price for item in db_cart.items)
    total_items = sum(item.quantity for item in db_cart.items)
    
    return CartResponse(
        id=db_cart.id,
        user_id=db_cart.user_id,
        items=items_with_products,
        total_items=total_items,
        subtotal=float(subtotal),  # Ensure it's a float
        created_at=db_cart.created_at,
        updated_at=db_cart.updated_at
    )
