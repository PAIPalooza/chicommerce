"""
Pydantic schemas for report API endpoints.

Defines request and response models for sales reports and analytics.
"""
from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SalesReportItemResponse(BaseModel):
    """
    Response model for a single sales report item.

    Represents aggregated sales data for a product and template version.
    """
    product_id: UUID = Field(..., description="Unique identifier of the product")
    product_name: str = Field(..., description="Name of the product")
    template_version: Optional[int] = Field(
        None,
        description="Template version used for customization (null if not specified)"
    )
    total_quantity: int = Field(
        ...,
        ge=0,
        description="Total quantity of items sold"
    )
    total_revenue: Decimal = Field(
        ...,
        ge=0,
        description="Total revenue generated from sales"
    )
    order_count: int = Field(
        ...,
        ge=0,
        description="Number of unique orders containing this product/template combination"
    )

    class Config:
        """Pydantic model configuration."""
        from_attributes = True
        json_encoders = {
            UUID: str,
            Decimal: str
        }


class SalesReportQueryParams(BaseModel):
    """
    Query parameters for sales report endpoint.

    Provides filtering and pagination options for report generation.
    """
    start: Optional[date] = Field(
        None,
        description="Start date for report (inclusive). Defaults to 30 days ago.",
        alias="start"
    )
    end: Optional[date] = Field(
        None,
        description="End date for report (inclusive). Defaults to today.",
        alias="end"
    )
    skip: int = Field(
        0,
        ge=0,
        description="Number of records to skip for pagination"
    )
    limit: int = Field(
        100,
        ge=1,
        le=1000,
        description="Maximum number of records to return (max 1000)"
    )

    @field_validator('end')
    @classmethod
    def validate_date_range(cls, end_value: Optional[date], info) -> Optional[date]:
        """
        Validate that end date is not before start date.

        Args:
            end_value: End date value
            info: Validation info containing other field values

        Returns:
            Validated end date

        Raises:
            ValueError: If end date is before start date
        """
        start_value = info.data.get('start')
        if start_value and end_value and end_value < start_value:
            raise ValueError("End date must be on or after start date")
        return end_value

    class Config:
        """Pydantic model configuration."""
        populate_by_name = True
