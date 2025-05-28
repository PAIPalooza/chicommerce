"""
OptionSet schemas for request/response validation.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator

from app.schemas.option import Option, OptionCreate, OptionUpdate


class OptionSetBase(BaseModel):
    """Base schema for OptionSet."""
    name: str = Field(..., max_length=100, description="Name of the option set")
    description: Optional[str] = Field(None, description="Description of the option set")
    is_required: bool = Field(True, description="Whether this option set is required")
    display_order: int = Field(0, description="Order in which the option set should be displayed")
    config: Optional[Dict[str, Any]] = Field(None, description="Additional configuration")


class OptionSetCreate(OptionSetBase):
    """Schema for creating a new OptionSet."""
    options: List[OptionCreate] = Field(default_factory=list, description="List of options in this set")


class OptionSetUpdate(BaseModel):
    """Schema for updating an existing OptionSet."""
    name: Optional[str] = Field(None, max_length=100, description="Name of the option set")
    description: Optional[str] = Field(None, description="Description of the option set")
    is_required: Optional[bool] = Field(None, description="Whether this option set is required")
    display_order: Optional[int] = Field(None, description="Order in which the option set should be displayed")
    config: Optional[Dict[str, Any]] = Field(None, description="Additional configuration")


from datetime import datetime

class OptionSetInDBBase(OptionSetBase):
    """Base schema for OptionSet in database."""
    id: UUID
    product_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class OptionSet(OptionSetInDBBase):
    """Schema for returning OptionSet data."""
    options: List[Option] = Field(default_factory=list, description="List of options in this set")


class OptionSetWithProduct(OptionSet):
    """Schema for returning OptionSet with product details."""
    product_name: str


class OptionSetWithOptionsCreate(OptionSetBase):
    """Schema for creating an OptionSet with options."""
    options: List[OptionCreate] = Field(..., description="List of options to create with this set")
