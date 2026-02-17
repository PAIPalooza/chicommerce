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


def get_zerodb_service():
    """
    Dependency for getting ZeroDB service instance.

    Returns:
        ZeroDBService: Configured ZeroDB service instance

    Raises:
        ValueError: If ZeroDB configuration is missing
    """
    from app.services.zerodb_service import ZeroDBService
    
    if not settings.ZERODB_PROJECT_ID:
        raise ValueError("ZERODB_PROJECT_ID must be configured")

    return ZeroDBService(
        project_id=settings.ZERODB_PROJECT_ID,
        api_token=settings.AINATIVE_API_TOKEN,
        api_url=settings.AINATIVE_API_URL
    )


def get_admin_user(api_key: str = Depends(api_key_header)):
    """
    Dependency for admin user authentication.
    
    This is an alias for get_admin_key to maintain compatibility with
    endpoints that were written expecting get_admin_user.
    
    Args:
        api_key: API key from header
        
    Returns:
        API key if valid
        
    Raises:
        HTTPException: 401 if API key is missing, 403 if API key is invalid
    """
    return get_admin_key(api_key)
