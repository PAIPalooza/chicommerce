"""API endpoints for cart functionality."""
from typing import List, Optional
from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app.api import deps
from app.core.config import settings
from app.crud import cart as crud_cart
from app.schemas.cart import (
    CartResponse, CartItemCreate, CartItemUpdate,
    CustomizationSessionCreate, CustomizationSessionUpdate, CustomizationSessionInDB,
    SessionStateResponse
)
from app.schemas.pricing import PriceBreakdown
from app.services.pricing_service import PricingService, TaxService, ShippingService

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


@router.patch("/customization-sessions/{product_id}", response_model=CustomizationSessionInDB)
async def validate_and_update_customization_session(
    product_id: UUID,
    session_in: CustomizationSessionUpdate,
    request: Request,
    db: Session = Depends(deps.get_db),
):
    """
    Validate and update a customization session with template constraint validation.

    This endpoint enforces all template constraints including:
    - Text length limits (min_length, max_length)
    - Image format restrictions
    - Color palette constraints
    - Unknown zone detection

    Args:
        product_id: UUID of the product being customized
        session_in: Customization data to validate and update
        request: HTTP request with session cookie
        db: Database session

    Returns:
        Updated CustomizationSession with validated data

    Raises:
        HTTPException 404: If session or template not found
        HTTPException 400: If validation fails with detailed error messages
    """
    from app.services.customization_validator import (
        CustomizationValidator,
        ValidationError
    )

    # Get session ID from cookie
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active session found"
        )

    # Get existing customization session
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

    # Validate customization data against template constraints
    validator = CustomizationValidator(db)

    try:
        is_valid, errors = validator.validate_customization_data(
            product_id=product_id,
            customization_data=session_in.customization_data
        )

        if not is_valid:
            # Return detailed validation errors
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="; ".join([f"{key}: {msg}" for key, msg in errors.items()])
            )

    except ValidationError as e:
        # Handle validator errors (e.g., template not found)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # If validation passes, update the session
    updated_session = crud_cart.update_customization_session(
        db,
        db_session=db_session,
        session_in=session_in
    )

    return updated_session


# Session State Endpoints

@router.get("/sessions/{session_key}", response_model=SessionStateResponse)
async def get_session_state(
    session_key: str,
    db: Session = Depends(deps.get_db),
):
    """
    Retrieve session state for resuming customization.

    Returns the customization session for the given session key,
    including current options and template version.

    Args:
        session_key: The session key to retrieve

    Returns:
        Session state with options and template version

    Raises:
        HTTPException 404: If session not found, expired, or inactive
    """
    from app.models.template import Template

    # Retrieve customization session by session key
    # (excludes sessions older than 30 days)
    session = crud_cart.get_customization_session_by_key(db, session_key=session_key)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired"
        )

    # Get the template to retrieve the version
    template = db.query(Template).filter(Template.id == session.template_id).first()
    template_version = template.version if template else None

    # Build response with template version
    session_response = SessionStateResponse(
        session_key=session.session_key,
        product_id=session.product_id,
        template_id=session.template_id,
        options=session.options,
        template_version=template_version,
        is_active=session.is_active,
        created_at=session.created_at,
        updated_at=session.updated_at
    )

    return session_response


def calculate_cart_pricing(db_cart) -> PriceBreakdown:
    """
    Calculate complete pricing breakdown for a cart.

    This function aggregates all cart items and calculates:
    - Base prices
    - Option surcharges from customization data
    - Tax (using stub service)
    - Shipping (using stub service)
    - Total

    Args:
        db_cart: Cart ORM model with items relationship loaded

    Returns:
        PriceBreakdown with complete pricing details
    """
    # Initialize pricing service with default tax and shipping services
    tax_service = TaxService()
    shipping_service = ShippingService()
    pricing_service = PricingService(
        tax_service=tax_service,
        shipping_service=shipping_service
    )

    # Prepare cart items for pricing calculation
    cart_items = []
    for item in db_cart.items:
        # Extract options from customization_data if present
        # In the future, this would map to actual Option models with price deltas
        options = []
        if item.customization_data:
            # For now, we assume customization_data might have option_surcharges
            # In a real implementation, we'd query the Option models
            option_surcharge = item.customization_data.get("option_surcharge", 0)
            if option_surcharge:
                options.append({
                    "name": "Customization",
                    "value": "Custom",
                    "price_delta": Decimal(str(option_surcharge))
                })

        cart_items.append({
            "base_price": Decimal(str(item.product.base_price)),
            "options": options,
            "quantity": item.quantity
        })

    # Calculate pricing
    if cart_items:
        price_calc = pricing_service.calculate_cart_total(
            items=cart_items,
            shipping_required=True
        )

        return PriceBreakdown(
            base_price=price_calc.base_price,
            option_surcharges=price_calc.option_surcharges,
            subtotal=price_calc.subtotal,
            tax=price_calc.tax,
            shipping=price_calc.shipping,
            total=price_calc.total
        )
    else:
        # Empty cart
        return PriceBreakdown(
            base_price=Decimal("0.00"),
            option_surcharges=Decimal("0.00"),
            subtotal=Decimal("0.00"),
            tax=Decimal("0.00"),
            shipping=Decimal("0.00"),
            total=Decimal("0.00")
        )


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

        # Calculate line_total for this item
        line_total = float(item.quantity * item.unit_price)

        item_dict = {
            'id': item.id,
            'cart_id': item.cart_id,
            'product_id': item.product_id,
            'quantity': item.quantity,
            'unit_price': float(item.unit_price),  # Ensure it's a float
            'customization_data': item.customization_data or {},
            'created_at': item.created_at,
            'updated_at': item.updated_at,
            'product': product_data,
            'line_total': line_total
        }
        items_with_products.append(CartItemWithProduct(**item_dict))

    subtotal = sum(item.quantity * item.unit_price for item in db_cart.items)
    total_items = sum(item.quantity for item in db_cart.items)

    # Calculate detailed pricing breakdown
    pricing = calculate_cart_pricing(db_cart)

    return CartResponse(
        id=db_cart.id,
        user_id=db_cart.user_id,
        items=items_with_products,
        total_items=total_items,
        subtotal=float(subtotal),  # Ensure it's a float
        created_at=db_cart.created_at,
        updated_at=db_cart.updated_at,
        pricing=pricing
    )
