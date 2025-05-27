"""
Product model module.
"""
import uuid
from typing import Optional, List
from datetime import datetime

from sqlalchemy import Column, String, Text, Boolean, DECIMAL, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.session import Base


class Product(Base):
    """
    Product model representing base product information.
    
    This model stores the core product data as specified in the data model.
    """
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    base_price = Column(DECIMAL(10, 2), nullable=False)
    media = Column(JSONB, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )

    # Relationships
    templates = relationship("Template", back_populates="product", cascade="all, delete-orphan")
    option_sets = relationship("OptionSet", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """String representation of Product."""
        return f"<Product {self.name}>"
