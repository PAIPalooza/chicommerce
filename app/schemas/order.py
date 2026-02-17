"""Order schemas for API request/response validation."""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.order import OrderStatus, PaymentProvider


# Base schemas
class OrderItemBase(BaseModel):
    """Base schema for order items."""
    product_id: UUID
    product_name: str
    quantity: int = Field(ge=1)
    unit_price: float = Field(ge=0)
    total_price: float = Field(ge=0)
    customization_data: Dict[str, Any] = Field(default_factory=dict)


class OrderItemCreate(OrderItemBase):
    """Schema for creating an order item."""
    pass


class OrderItemResponse(OrderItemBase):
    """Schema for order item responses."""
    id: UUID
    order_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


# Order schemas
class OrderBase(BaseModel):
    """Base schema for orders."""
    user_id: Optional[UUID] = None
    session_id: str
    customer_email: EmailStr
    customer_phone: Optional[str] = None
    shipping_address: Dict[str, Any]
    billing_address: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    currency: str = "USD"

    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency code."""
        if len(v) != 3:
            raise ValueError("Currency must be a 3-letter ISO code")
        return v.upper()


class OrderCreate(OrderBase):
    """Schema for creating an order."""
    items: List[OrderItemCreate]
    subtotal: float = Field(ge=0)
    tax: float = Field(ge=0, default=0.0)
    shipping_cost: float = Field(ge=0, default=0.0)
    total: float = Field(ge=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('total')
    @classmethod
    def validate_total(cls, v: float, info) -> float:
        """Validate that total matches sum of components."""
        if 'subtotal' in info.data and 'tax' in info.data and 'shipping_cost' in info.data:
            expected = info.data['subtotal'] + info.data['tax'] + info.data['shipping_cost']
            if abs(v - expected) > 0.01:  # Allow for floating point precision
                raise ValueError(f"Total must equal subtotal + tax + shipping_cost. Expected {expected}, got {v}")
        return v


class OrderUpdate(BaseModel):
    """Schema for updating an order."""
    status: Optional[OrderStatus] = None
    shipping_address: Optional[Dict[str, Any]] = None
    billing_address: Optional[Dict[str, Any]] = None
    customer_phone: Optional[str] = None
    notes: Optional[str] = None


class OrderResponse(OrderBase):
    """Schema for order responses."""
    id: UUID
    status: str
    payment_provider: Optional[str] = None
    payment_intent_id: Optional[str] = None
    payment_status: Optional[str] = None
    subtotal: float
    tax: float
    shipping_cost: float
    total: float
    tracking_url: Optional[str] = None
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    paid_at: Optional[datetime] = None
    items: List[OrderItemResponse] = []

    model_config = {"from_attributes": True}


# Payment webhook schemas
class WebhookEventBase(BaseModel):
    """Base schema for webhook events."""
    event_id: str
    event_type: str
    provider: str


class StripeWebhookEvent(WebhookEventBase):
    """Schema for Stripe webhook events."""
    provider: str = Field(default=PaymentProvider.STRIPE)
    payload: Dict[str, Any]

    @field_validator('event_type')
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        """Validate Stripe event types."""
        valid_types = [
            'payment_intent.succeeded',
            'payment_intent.payment_failed',
            'payment_intent.canceled',
            'payment_intent.processing',
            'charge.succeeded',
            'charge.failed',
            'charge.refunded'
        ]
        if v not in valid_types:
            raise ValueError(f"Invalid Stripe event type: {v}")
        return v


class PayPalWebhookEvent(WebhookEventBase):
    """Schema for PayPal webhook events."""
    provider: str = Field(default=PaymentProvider.PAYPAL)
    payload: Dict[str, Any]

    @field_validator('event_type')
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        """Validate PayPal event types."""
        valid_types = [
            'PAYMENT.CAPTURE.COMPLETED',
            'PAYMENT.CAPTURE.DENIED',
            'PAYMENT.CAPTURE.REFUNDED',
            'CHECKOUT.ORDER.APPROVED',
            'CHECKOUT.ORDER.COMPLETED'
        ]
        if v not in valid_types:
            raise ValueError(f"Invalid PayPal event type: {v}")
        return v


class WebhookProcessingResult(BaseModel):
    """Schema for webhook processing results."""
    success: bool
    message: str
    order_id: Optional[UUID] = None
    event_id: str
    processed: bool


# Payment event schemas
class PaymentEventResponse(BaseModel):
    """Schema for payment event responses."""
    id: UUID
    order_id: UUID
    event_id: str
    event_type: str
    provider: str
    payment_intent_id: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    processed: bool
    processed_at: Optional[datetime] = None
    processing_error: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# Order status update schema
class OrderStatusUpdate(BaseModel):
    """Schema for order status updates."""
    status: OrderStatus
    payment_intent_id: Optional[str] = None
    payment_status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# Checkout schemas
class CheckoutRequest(BaseModel):
    """Schema for checkout request."""
    customer_email: EmailStr
    customer_phone: Optional[str] = None
    shipping_address: Dict[str, Any]
    billing_address: Optional[Dict[str, Any]] = None
    payment_provider: str = Field(default=PaymentProvider.STRIPE)

    @field_validator('payment_provider')
    @classmethod
    def validate_payment_provider(cls, v: str) -> str:
        """Validate payment provider is supported."""
        valid_providers = [p.value for p in PaymentProvider]
        if v not in valid_providers:
            raise ValueError(f"Payment provider must be one of: {', '.join(valid_providers)}")
        return v


class CheckoutResponse(BaseModel):
    """Schema for checkout response."""
    order_id: UUID
    payment_token: str = Field(..., description="Payment intent token/ID for completing payment")
    status: str
    total: float
    currency: str = "USD"

    model_config = {"from_attributes": True}
