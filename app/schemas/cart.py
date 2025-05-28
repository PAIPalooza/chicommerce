"""Pydantic models for cart-related schemas."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, validator

from app.schemas.product import ProductBase


class CartItemBase(BaseModel):
    """Base schema for cart items."""
    product_id: UUID
    quantity: int = Field(..., gt=0, description="Quantity must be greater than 0")
    unit_price: float = Field(..., gt=0, description="Unit price must be greater than 0")
    customization_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Customization data for the product"
    )

    @validator('quantity')
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        return v


class CartItemCreate(CartItemBase):
    """Schema for creating a new cart item."""
    pass


class CartItemUpdate(BaseModel):
    """Schema for updating an existing cart item."""
    quantity: Optional[int] = Field(None, gt=0, description="New quantity, must be greater than 0")
    customization_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Updated customization data for the product"
    )


class CartItemInDBBase(CartItemBase):
    """Base schema for cart items stored in the database."""
    id: UUID
    cart_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class CartItemWithProduct(CartItemInDBBase):
    """Cart item with product details."""
    product: ProductBase


class CartBase(BaseModel):
    """Base schema for carts."""
    user_id: Optional[UUID] = None
    session_id: str


class CartCreate(CartBase):
    """Schema for creating a new cart."""
    pass


class CartInDBBase(CartBase):
    """Base schema for carts stored in the database."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    items: List[CartItemWithProduct] = []

    class Config:
        orm_mode = True


class CartUpdate(BaseModel):
    """Schema for updating a cart."""
    user_id: Optional[UUID] = None


class CustomizationSessionBase(BaseModel):
    """Base schema for customization sessions."""
    product_id: UUID
    customization_data: Dict[str, Any] = Field(default_factory=dict)


class CustomizationSessionCreate(CustomizationSessionBase):
    """Schema for creating a new customization session."""
    session_id: str


class CustomizationSessionUpdate(BaseModel):
    """Schema for updating a customization session."""
    customization_data: Dict[str, Any]
    is_active: Optional[bool] = None


class CustomizationSessionInDB(CustomizationSessionBase):
    """Schema for customization sessions stored in the database."""
    id: UUID
    session_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class CartResponse(BaseModel):
    """Response schema for cart operations."""
    id: UUID
    user_id: Optional[UUID]
    items: List[CartItemWithProduct]
    total_items: int
    subtotal: float
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
