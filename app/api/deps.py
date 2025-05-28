"""
Dependency injection for API endpoints.
"""
from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.config import settings

# Configure API key header to allow custom error handling
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_db_session() -> Generator:
    """
    Dependency for getting DB session.
    
    Yields:
        Session: Database session
    """
    db = None
    try:
        db = next(get_db())
        yield db
    finally:
        if db:
            db.close()


def get_admin_key(api_key: str = Depends(api_key_header)) -> str:
    """
    Dependency for checking API key authentication for admin routes.
    
    Args:
        api_key: API key from header
        
    Returns:
        API key if valid
        
    Raises:
        HTTPException: 401 if API key is missing, 403 if API key is invalid
    """
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required",
        )
    if api_key != settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key",
        )
    return api_key
