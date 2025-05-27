"""
Template schema module for request/response validation.
"""
from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, validator


class CustomizationZoneBase(BaseModel):
    """Base schema for CustomizationZone data."""
    key: str = Field(..., min_length=1, max_length=100, description="Zone identifier (e.g., 'text_line1')")
    type: str = Field(..., description="Zone type (text, image, color, shape)")
    config: Optional[Dict[str, Any]] = Field(None, description="Zone-specific settings (maxLength, formats)")
    order_index: int = Field(..., ge=0, description="Determines rendering order")


class CustomizationZoneCreate(CustomizationZoneBase):
    """Schema for creating a new CustomizationZone."""
    pass


class CustomizationZone(CustomizationZoneBase):
    """Schema for CustomizationZone response."""
    id: UUID
    template_id: UUID

    class Config:
        """Pydantic config."""
        orm_mode = True


class TemplateBase(BaseModel):
    """Base schema for Template data."""
    product_id: UUID = Field(..., description="ID of the product this template belongs to")
    version: int = Field(..., gt=0, description="Template version (incremental)")
    definition: Dict[str, Any] = Field(..., description="JSON schema for zones (text, image, color, etc.)")
    is_default: bool = Field(False, description="Flag for default template per product")


class TemplateCreate(TemplateBase):
    """Schema for creating a new Template."""
    customization_zones: Optional[List[CustomizationZoneCreate]] = Field(None, description="Customization zones within the template")


class TemplateUpdate(BaseModel):
    """Schema for updating a Template."""
    definition: Optional[Dict[str, Any]] = Field(None, description="JSON schema for zones")
    is_default: Optional[bool] = Field(None, description="Flag for default template per product")


class TemplateInDBBase(TemplateBase):
    """Base schema for Template already in the database."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""
        orm_mode = True


class Template(TemplateInDBBase):
    """Schema for Template response."""
    customization_zones: List[CustomizationZone] = Field([], description="Customization zones within the template")
