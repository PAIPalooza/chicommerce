"""
Option schemas for request/response validation.
"""
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator


class OptionBase(BaseModel):
    """Base schema for Option."""
    name: str = Field(..., max_length=100, description="Display name of the option")
    value: str = Field(..., max_length=255, description="Value to be used for this option")
    display_order: int = Field(0, description="Order in which the option should be displayed")
    additional_price: int = Field(0, description="Additional price in cents")
    is_default: bool = Field(False, description="Whether this is the default option")
    config: Optional[Dict[str, Any]] = Field(None, description="Additional configuration")


class OptionCreate(OptionBase):
    """Schema for creating a new Option."""
    pass


class OptionUpdate(BaseModel):
    """Schema for updating an existing Option."""
    name: Optional[str] = Field(None, max_length=100, description="Display name of the option")
    value: Optional[str] = Field(None, max_length=255, description="Value to be used for this option")
    display_order: Optional[int] = Field(None, description="Order in which the option should be displayed")
    additional_price: Optional[int] = Field(None, description="Additional price in cents")
    is_default: Optional[bool] = Field(None, description="Whether this is the default option")
    config: Optional[Dict[str, Any]] = Field(None, description="Additional configuration")


from datetime import datetime

class OptionInDBBase(OptionBase):
    """Base schema for Option in database."""
    id: UUID
    option_set_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class Option(OptionInDBBase):
    """Schema for returning Option data."""
    pass
