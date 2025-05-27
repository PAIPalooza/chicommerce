"""
OptionSet model module.
"""
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.session import Base


class OptionSet(Base):
    """
    OptionSet model representing a set of options for a product.
    
    This model defines a set of options that can be selected for a product,
    such as color, size, or material.
    """
    __tablename__ = "option_sets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_required = Column(Boolean, default=True, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)
    config = Column(JSONB, nullable=True)  # For additional configuration
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )

    # Relationships
    product = relationship("Product", back_populates="option_sets")
    options = relationship("Option", back_populates="option_set", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """String representation of OptionSet."""
        return f"<OptionSet {self.name} (Product ID: {self.product_id})>"


class Option(Base):
    """
    Option model representing a selectable option within an OptionSet.
    
    This model defines an individual option that can be selected within an OptionSet.
    """
    __tablename__ = "options"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    option_set_id = Column(UUID(as_uuid=True), ForeignKey("option_sets.id"), nullable=False)
    name = Column(String(100), nullable=False)
    value = Column(String(255), nullable=False)  # The actual value to be used
    display_order = Column(Integer, default=0, nullable=False)
    additional_price = Column(Integer, default=0, nullable=False)  # Price adjustment in cents
    is_default = Column(Boolean, default=False, nullable=False)
    config = Column(JSONB, nullable=True)  # For additional configuration
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )

    # Relationships
    option_set = relationship("OptionSet", back_populates="options")

    def __repr__(self) -> str:
        """String representation of Option."""
        return f"<Option {self.name}={self.value} (Set ID: {self.option_set_id})>"
