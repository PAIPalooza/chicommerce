"""
Security utilities.
"""
import secrets
from typing import Optional

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app.core.config import settings

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str) -> bool:
    """
    Verify if the provided API key is valid.
    
    Args:
        api_key: The API key to verify
        
    Returns:
        True if valid, False otherwise
    """
    # In a real-world scenario, this would check against a database of valid API keys
    # For simplicity, we're just checking against the configured admin API key
    return api_key == settings.ADMIN_API_KEY


def generate_api_key() -> str:
    """
    Generate a secure API key.
    
    Returns:
        A new API key
    """
    return secrets.token_urlsafe(32)


def get_current_api_key(
    api_key: str = Security(API_KEY_HEADER),
) -> str:
    """
    Get and validate the current API key.
    
    Args:
        api_key: The API key from the request header
        
    Returns:
        The validated API key
        
    Raises:
        HTTPException: If the API key is invalid or missing
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key is missing",
        )
    
    if not verify_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
    
    return api_key
