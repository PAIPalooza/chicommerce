"""WebhookLog schemas for API request/response validation."""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class WebhookLogBase(BaseModel):
    """Base schema for webhook logs."""
    event_type: str = Field(..., description="Type of webhook event")
    event_id: Optional[str] = Field(None, description="External event ID if available")
    url: str = Field(..., description="URL where webhook was sent")
    http_method: str = Field(default="POST", description="HTTP method used")


class WebhookLogCreate(WebhookLogBase):
    """Schema for creating a webhook log."""
    payload: Optional[str] = Field(None, description="Request payload sent")
    headers: Optional[str] = Field(None, description="Request headers sent")
    response_status: Optional[int] = Field(None, description="HTTP response status code")
    response_body: Optional[str] = Field(None, description="Response body received")
    error_message: Optional[str] = Field(None, description="Error message if delivery failed")
    response_time_ms: Optional[int] = Field(None, description="Response time in milliseconds")
    retry_count: int = Field(default=0, description="Number of retry attempts")
    is_success: bool = Field(default=False, description="Whether delivery was successful")

    @field_validator('response_status')
    @classmethod
    def validate_response_status(cls, v: Optional[int]) -> Optional[int]:
        """Validate HTTP status code range."""
        if v is not None and (v < 100 or v > 599):
            raise ValueError("HTTP status code must be between 100 and 599")
        return v


class WebhookLogResponse(WebhookLogBase):
    """Schema for webhook log responses."""
    id: UUID
    payload: Optional[str] = None
    headers: Optional[str] = None
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    sent_at: datetime
    response_time_ms: Optional[int] = None
    retry_count: int
    is_success: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class WebhookLogListResponse(BaseModel):
    """Schema for paginated webhook log list responses."""
    items: List[WebhookLogResponse]
    total: int = Field(..., description="Total number of webhook logs matching filters")
    limit: int = Field(..., description="Maximum number of items per page")
    offset: int = Field(..., description="Number of items skipped")
    has_more: bool = Field(..., description="Whether there are more items to fetch")


class WebhookLogQueryParams(BaseModel):
    """Schema for webhook log query parameters."""
    event: Optional[str] = Field(None, description="Filter by event type (e.g., 'order.created')")
    status: Optional[int] = Field(None, description="Filter by HTTP response status code")
    success: Optional[bool] = Field(None, description="Filter by success/failure status")
    limit: int = Field(default=50, ge=1, le=100, description="Number of items to return (max 100)")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: Optional[int]) -> Optional[int]:
        """Validate HTTP status code range."""
        if v is not None and (v < 100 or v > 599):
            raise ValueError("HTTP status code must be between 100 and 599")
        return v
