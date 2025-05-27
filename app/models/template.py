"""
Template model module.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.session import Base


class Template(Base):
    """
    Template model defining customization options for products.
    
    This model stores the template definitions including customization zones
    and version tracking for products.
    """
    __tablename__ = "templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    definition = Column(JSONB, nullable=False)
    is_default = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )

    # Relationships
    product = relationship("Product", back_populates="templates")
    customization_zones = relationship("CustomizationZone", back_populates="template", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        UniqueConstraint('product_id', 'version', name='uq_template_product_version'),
    )

    def __repr__(self) -> str:
        """String representation of Template."""
        return f"<Template for Product {self.product_id}, v{self.version}>"


class CustomizationZone(Base):
    """
    CustomizationZone model defining individual customizable zones within a template.
    
    This model stores specific zones like text fields, image overlays, color pickers, etc.
    """
    __tablename__ = "customization_zones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(UUID(as_uuid=True), ForeignKey("templates.id", ondelete="CASCADE"), nullable=False)
    key = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)
    config = Column(JSONB, nullable=True)
    order_index = Column(Integer, nullable=False)
    
    # Relationships
    template = relationship("Template", back_populates="customization_zones")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('template_id', 'key', name='uq_zone_template_key'),
    )

    def __repr__(self) -> str:
        """String representation of CustomizationZone."""
        return f"<CustomizationZone {self.key} ({self.type})>"
