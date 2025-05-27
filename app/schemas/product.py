"""
Product schema module for request/response validation.
"""
from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel, Field, validator


class ProductBase(BaseModel):
    """Base schema for Product data."""
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    base_price: Decimal = Field(..., ge=0, description="Base price of the product")
    media: Optional[Dict[str, Any]] = Field(None, description="Product media (images, videos)")
    is_active: bool = Field(True, description="Whether the product is active")


class ProductCreate(ProductBase):
    """Schema for creating a new Product."""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating a Product."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    base_price: Optional[Decimal] = Field(None, ge=0, description="Base price of the product")
    media: Optional[Dict[str, Any]] = Field(None, description="Product media (images, videos)")
    is_active: Optional[bool] = Field(None, description="Whether the product is active")


class ProductInDBBase(ProductBase):
    """Base schema for Product already in the database."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""
        orm_mode = True


class Product(ProductInDBBase):
    """Schema for Product response."""
    pass


class ProductWithDefaultTemplate(ProductInDBBase):
    """Schema for Product with its default template."""
    default_template: Optional[Dict[str, Any]] = None
