"""
Authentication API endpoints.

This module provides REST API endpoints for user authentication operations:
- User registration
- User login
- Token refresh
- Current user profile retrieval
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, Header
from fastapi.responses import JSONResponse

from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenRefreshRequest,
    TokenResponse,
    UserResponse,
    UserRegisterResponse,
    ErrorResponse,
    ValidationErrorResponse
)
from app.services.auth_service import auth_service

router = APIRouter()


@router.post(
    "/register",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "User successfully registered",
            "model": UserRegisterResponse
        },
        409: {
            "description": "Email already registered",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"detail": "Email already registered"}
                }
            }
        },
        422: {
            "description": "Validation error",
            "model": ValidationErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "email"],
                                "msg": "value is not a valid email address",
                                "type": "value_error.email"
                            }
                        ]
                    }
                }
            }
        },
        503: {
            "description": "Authentication service unavailable",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"detail": "Authentication service timeout"}
                }
            }
        }
    },
    summary="Register a new user",
    description="Create a new user account with email, password, and name. "
                "Password must be at least 8 characters and contain uppercase, lowercase, and digit.",
    tags=["Authentication"]
)
async def register(user_data: UserRegisterRequest) -> UserRegisterResponse:
    """
    Register a new user account.

    This endpoint creates a new user account in the AINative authentication system.
    The password must meet security requirements (min 8 chars, uppercase, lowercase, digit).

    Args:
        user_data: User registration data (email, password, name)

    Returns:
        UserRegisterResponse: Created user data with optional authentication tokens

    Raises:
        HTTPException: 409 if email already exists, 422 for validation errors, 503 if service unavailable
    """
    result = await auth_service.register_user(
        email=user_data.email,
        password=user_data.password,
        name=user_data.name
    )
    return UserRegisterResponse(**result)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Login successful",
            "model": TokenResponse
        },
        401: {
            "description": "Invalid credentials",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid email or password"}
                }
            }
        },
        422: {
            "description": "Validation error",
            "model": ValidationErrorResponse
        },
        503: {
            "description": "Authentication service unavailable",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"detail": "Authentication service timeout"}
                }
            }
        }
    },
    summary="Login user",
    description="Authenticate user with email and password to obtain access and refresh tokens.",
    tags=["Authentication"]
)
async def login(credentials: UserLoginRequest) -> TokenResponse:
    """
    Login user and obtain authentication tokens.

    This endpoint authenticates a user with email and password and returns
    JWT access and refresh tokens for subsequent API calls.

    Args:
        credentials: User login credentials (email, password)

    Returns:
        TokenResponse: Access token, refresh token, token type, and expiration

    Raises:
        HTTPException: 401 if credentials are invalid, 503 if service unavailable
    """
    result = await auth_service.login(
        email=credentials.email,
        password=credentials.password
    )
    return TokenResponse(**result)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Token refreshed successfully",
            "model": TokenResponse
        },
        401: {
            "description": "Invalid or expired refresh token",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid or expired refresh token"}
                }
            }
        },
        422: {
            "description": "Validation error",
            "model": ValidationErrorResponse
        },
        503: {
            "description": "Authentication service unavailable",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"detail": "Authentication service timeout"}
                }
            }
        }
    },
    summary="Refresh access token",
    description="Use a refresh token to obtain a new access token without re-authenticating.",
    tags=["Authentication"]
)
async def refresh_token(token_data: TokenRefreshRequest) -> TokenResponse:
    """
    Refresh access token using refresh token.

    This endpoint allows users to obtain a new access token using a valid refresh token,
    extending their session without requiring re-authentication.

    Args:
        token_data: Refresh token data

    Returns:
        TokenResponse: New access token and possibly new refresh token

    Raises:
        HTTPException: 401 if refresh token is invalid, 503 if service unavailable
    """
    result = await auth_service.refresh_token(
        refresh_token=token_data.refresh_token
    )
    return TokenResponse(**result)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "User profile retrieved successfully",
            "model": UserResponse
        },
        401: {
            "description": "Invalid or expired access token",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid or expired token"}
                }
            }
        },
        503: {
            "description": "Authentication service unavailable",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"detail": "Authentication service timeout"}
                }
            }
        }
    },
    summary="Get current user profile",
    description="Retrieve the profile information of the currently authenticated user.",
    tags=["Authentication"]
)
async def get_current_user(
    authorization: str = Header(
        ...,
        description="Bearer token in format: Bearer <access_token>",
        json_schema_extra={"example": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
    )
) -> UserResponse:
    """
    Get current authenticated user profile.

    This endpoint retrieves the profile information of the user associated
    with the provided access token in the Authorization header.

    Args:
        authorization: Authorization header with Bearer token

    Returns:
        UserResponse: Current user profile data

    Raises:
        HTTPException: 401 if token is invalid or missing, 503 if service unavailable
    """
    # Extract bearer token
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected: Bearer <token>"
        )

    access_token = authorization.replace("Bearer ", "").strip()

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token is required"
        )

    result = await auth_service.get_current_user(access_token=access_token)
    return UserResponse(**result)
