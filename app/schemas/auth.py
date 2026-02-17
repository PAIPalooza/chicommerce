"""
Authentication schemas for request/response validation.
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegisterRequest(BaseModel):
    """Request schema for user registration."""

    email: EmailStr = Field(
        ...,
        description="User email address",
        json_schema_extra={"example": "user@example.com"}
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password (minimum 8 characters)",
        json_schema_extra={"example": "SecurePass123!"}
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="User full name",
        json_schema_extra={"example": "John Doe"}
    )

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets minimum security requirements."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty or just whitespace."""
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()


class UserLoginRequest(BaseModel):
    """Request schema for user login."""

    email: EmailStr = Field(
        ...,
        description="User email address",
        json_schema_extra={"example": "user@example.com"}
    )
    password: str = Field(
        ...,
        description="User password",
        json_schema_extra={"example": "SecurePass123!"}
    )


class TokenRefreshRequest(BaseModel):
    """Request schema for token refresh."""

    refresh_token: str = Field(
        ...,
        description="JWT refresh token",
        json_schema_extra={"example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
    )


class TokenResponse(BaseModel):
    """Response schema for authentication tokens."""

    access_token: str = Field(
        ...,
        description="JWT access token for API authentication",
        json_schema_extra={"example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
    )
    refresh_token: Optional[str] = Field(
        None,
        description="JWT refresh token for obtaining new access tokens",
        json_schema_extra={"example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer')",
        json_schema_extra={"example": "bearer"}
    )
    expires_in: Optional[int] = Field(
        None,
        description="Token expiration time in seconds",
        json_schema_extra={"example": 3600}
    )


class UserResponse(BaseModel):
    """Response schema for user data."""

    user_id: str = Field(
        ...,
        description="Unique user identifier",
        json_schema_extra={"example": "usr_abc123"}
    )
    email: EmailStr = Field(
        ...,
        description="User email address",
        json_schema_extra={"example": "user@example.com"}
    )
    name: str = Field(
        ...,
        description="User full name",
        json_schema_extra={"example": "John Doe"}
    )
    is_active: Optional[bool] = Field(
        True,
        description="Whether the user account is active",
        json_schema_extra={"example": True}
    )
    created_at: Optional[str] = Field(
        None,
        description="Account creation timestamp",
        json_schema_extra={"example": "2024-01-01T00:00:00Z"}
    )


class UserRegisterResponse(UserResponse):
    """Response schema for user registration."""

    access_token: Optional[str] = Field(
        None,
        description="JWT access token (if auto-login is enabled)",
        json_schema_extra={"example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
    )
    refresh_token: Optional[str] = Field(
        None,
        description="JWT refresh token (if auto-login is enabled)",
        json_schema_extra={"example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
    )


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    detail: str = Field(
        ...,
        description="Error message describing what went wrong",
        json_schema_extra={"example": "Invalid credentials"}
    )


class ValidationErrorDetail(BaseModel):
    """Validation error detail."""

    loc: list[str] = Field(
        ...,
        description="Location of the validation error",
        json_schema_extra={"example": ["body", "email"]}
    )
    msg: str = Field(
        ...,
        description="Validation error message",
        json_schema_extra={"example": "field required"}
    )
    type: str = Field(
        ...,
        description="Error type",
        json_schema_extra={"example": "value_error.missing"}
    )


class ValidationErrorResponse(BaseModel):
    """Validation error response schema."""

    detail: list[ValidationErrorDetail] = Field(
        ...,
        description="List of validation errors"
    )
