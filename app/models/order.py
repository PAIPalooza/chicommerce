"""Order models for the e-commerce platform."""
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, JSON, String, Numeric, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class OrderStatus(str, Enum):
    """Order status enumeration with state machine transitions."""
    CREATED = "created"  # Initial state after order creation
    PENDING_PAYMENT = "pending_payment"  # Awaiting payment confirmation
    PAID = "paid"  # Payment confirmed successfully
    FAILED = "failed"  # Payment failed
    PROCESSING = "processing"  # Order being processed
    SHIPPED = "shipped"  # Order shipped
    DELIVERED = "delivered"  # Order delivered
    CANCELLED = "cancelled"  # Order cancelled
    REFUNDED = "refunded"  # Order refunded


class PaymentProvider(str, Enum):
    """Supported payment providers."""
    STRIPE = "stripe"
    PAYPAL = "paypal"


class Order(Base):
    """Order model representing a customer purchase."""
    __tablename__ = "orders"

    id: Mapped[UUID] = mapped_column(primary_key=True, index=True, default=uuid4)
    cart_id: Mapped[UUID] = mapped_column(ForeignKey("carts.id"), index=True, nullable=False)
    user_id: Mapped[Optional[UUID]] = mapped_column(index=True, nullable=True)  # Null for guest checkout
    session_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=OrderStatus.CREATED, nullable=False, index=True)

    # Payment information
    payment_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    payment_intent_id: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    payment_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Financial details
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    tax: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0, nullable=False)
    shipping_cost: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0, nullable=False)
    total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    # Shipping information
    shipping_address: Mapped[dict] = mapped_column(JSON, nullable=False)
    billing_address: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    tracking_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, index=True)

    # Contact information
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    customer_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Order notes and metadata
    notes: Mapped[Optional[str]] = mapped_column(nullable=True)
    order_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    paid_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    cart: Mapped["Cart"] = relationship(back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    payment_events: Mapped[List["PaymentEvent"]] = relationship(back_populates="order", cascade="all, delete-orphan")

    # Indexes for performance
    __table_args__ = (
        Index('idx_order_status_created', 'status', 'created_at'),
        Index('idx_order_payment_intent', 'payment_intent_id'),
    )

    def __repr__(self) -> str:
        return f"<Order {self.id} status={self.status}>"


class OrderItem(Base):
    """Individual item within an order."""
    __tablename__ = "order_items"

    id: Mapped[UUID] = mapped_column(primary_key=True, index=True, default=uuid4)
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id"), index=True, nullable=False)

    # Item details
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)  # Snapshot at time of order
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    total_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    # Customization data
    customization_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()

    def __repr__(self) -> str:
        return f"<OrderItem {self.id} order={self.order_id}>"


class PaymentEvent(Base):
    """Payment event log for audit trail and idempotency."""
    __tablename__ = "payment_events"

    id: Mapped[UUID] = mapped_column(primary_key=True, index=True, default=uuid4)
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)

    # Event details
    event_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)  # Provider event ID for idempotency
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)

    # Payment information
    payment_intent_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    amount: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)

    # Event payload and processing
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    processed: Mapped[bool] = mapped_column(default=False, nullable=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    processing_error: Mapped[Optional[str]] = mapped_column(nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)

    # Relationships
    order: Mapped["Order"] = relationship(back_populates="payment_events")

    # Indexes for performance and idempotency
    __table_args__ = (
        Index('idx_payment_event_provider', 'provider', 'event_type'),
        Index('idx_payment_event_processed', 'processed', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<PaymentEvent {self.event_id} type={self.event_type}>"
