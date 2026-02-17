"""
Pydantic schemas for CustomizationSession.

This module defines request and response schemas for session management.
"""
from uuid import UUID
from typing import Dict, Any
from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    """Schema for creating a new customization session."""

    product_id: UUID = Field(..., description="ID of the product being customized")
    template_id: UUID = Field(..., description="ID of the template to use for customization")

    model_config = {
        "json_schema_extra": {
            "example": {
                "product_id": "123e4567-e89b-12d3-a456-426614174000",
                "template_id": "123e4567-e89b-12d3-a456-426614174001"
            }
        }
    }


class SessionResponse(BaseModel):
    """Schema for customization session response."""

    session_id: UUID = Field(..., description="Unique session identifier")
    session_key: str = Field(..., description="Secure session access key")
    product_id: UUID = Field(..., description="ID of the product being customized")
    template_id: UUID = Field(..., description="ID of the template used for customization")
    options: Dict[str, Any] = Field(default_factory=dict, description="Customization options data")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174002",
                "session_key": "sess_a1b2c3d4e5f6g7h8i9j0",
                "product_id": "123e4567-e89b-12d3-a456-426614174000",
                "template_id": "123e4567-e89b-12d3-a456-426614174001",
                "options": {}
            }
        }
    }
