"""Pydantic models for pricing-related schemas."""
from decimal import Decimal
from pydantic import BaseModel, Field


class PriceBreakdown(BaseModel):
    """Schema for detailed price breakdown."""
    base_price: Decimal = Field(..., description="Base price before any surcharges")
    option_surcharges: Decimal = Field(..., description="Total surcharges from customization options")
    subtotal: Decimal = Field(..., description="Base price + option surcharges")
    tax: Decimal = Field(..., description="Tax amount")
    shipping: Decimal = Field(..., description="Shipping cost")
    total: Decimal = Field(..., description="Final total price")

    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


class CartItemPricing(BaseModel):
    """Pricing information for a single cart item."""
    item_id: str
    base_price: Decimal
    option_surcharges: Decimal
    quantity: int
    line_total: Decimal

    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }


class CartPricingSummary(BaseModel):
    """Complete pricing summary for a cart."""
    items: list[CartItemPricing]
    breakdown: PriceBreakdown

    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)
        }
