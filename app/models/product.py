"""
Product model module.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String, Text, Boolean, Numeric, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class Product(Base):
    """
    Product model representing base product information.
    
    This model stores the core product data as specified in the data model.
    """
    __tablename__ = "products"

    id: Mapped[UUID] = mapped_column(primary_key=True, index=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    base_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    media: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    templates: Mapped[List["Template"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    option_sets: Mapped[List["OptionSet"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    cart_items: Mapped[List["CartItem"]] = relationship(back_populates="product")
    customization_sessions: Mapped[List["CustomizationSession"]] = relationship(back_populates="product")

    def __repr__(self) -> str:
        """String representation of Product."""
        return f"<Product {self.name}>"
