"""Cart models for the e-commerce platform."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Cart(Base):
    """Shopping cart model."""
    __tablename__ = "carts"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, index=True, default=uuid4)
    user_id: Mapped[Optional[UUID]] = mapped_column(index=True, nullable=True)  # Null for guest users
    session_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items: Mapped[List["CartItem"]] = relationship(back_populates="cart", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Cart {self.id}>"


class CartItem(Base):
    """Item in a shopping cart."""
    __tablename__ = "cart_items"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, index=True, default=uuid4)
    cart_id: Mapped[UUID] = mapped_column(ForeignKey("carts.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id"), index=True, nullable=False)
    quantity: Mapped[int] = mapped_column(default=1, nullable=False)
    unit_price: Mapped[float] = mapped_column(nullable=False)
    customization_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    cart: Mapped["Cart"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="cart_items")
    
    def __repr__(self) -> str:
        return f"<CartItem {self.id} for Cart {self.cart_id}>"


class CustomizationSession(Base):
    """Tracks the state of a product customization session."""
    __tablename__ = "customization_sessions"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, index=True, default=uuid4)
    session_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id"), index=True, nullable=False)
    customization_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product: Mapped["Product"] = relationship(back_populates="customization_sessions")
    
    def __repr__(self) -> str:
        return f"<CustomizationSession {self.id} for Product {self.product_id}>"
