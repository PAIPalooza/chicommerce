"""
Session management API endpoints.

This module handles creating and retrieving customization sessions
for product customization workflows.
"""
import secrets
from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.cart import CustomizationSession
from app.models.product import Product
from app.models.template import Template
from app.schemas.session import SessionCreate, SessionResponse

router = APIRouter()


def generate_session_key() -> str:
    """
    Generate a secure, URL-safe session key.

    Returns:
        A session key with the format: sess_{random_token}

    Security:
        Uses secrets.token_urlsafe for cryptographically secure random tokens.
        The token is 32 bytes, which becomes ~43 characters when base64url encoded.
    """
    token = secrets.token_urlsafe(32)
    return f"sess_{token}"


@router.post(
    "/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new customization session",
    description="Creates a new customization session for a product with an empty options object",
)
async def create_session(
    session_data: SessionCreate,
    db: Annotated[Session, Depends(deps.get_db_session)]
) -> SessionResponse:
    """
    Create a new customization session.

    This endpoint initializes a new customization session for a product.
    The session starts with empty options that can be updated later.

    Args:
        session_data: Request body containing product_id and template_id
        db: Database session dependency

    Returns:
        SessionResponse containing session_id, session_key, product_id,
        template_id, and empty options

    Raises:
        HTTPException 404: If product or template doesn't exist
        HTTPException 422: If validation fails

    Security:
        - Generates cryptographically secure session_key
        - session_key is unique and URL-safe
    """
    # Verify product exists
    product = db.query(Product).filter(Product.id == session_data.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {session_data.product_id} not found"
        )

    # Verify template exists
    template = db.query(Template).filter(Template.id == session_data.template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with id {session_data.template_id} not found"
        )

    # Generate a unique, secure session key
    session_key = generate_session_key()

    # Ensure session key is unique (extremely unlikely collision, but safe guard)
    while db.query(CustomizationSession).filter(
        CustomizationSession.session_key == session_key
    ).first() is not None:
        session_key = generate_session_key()

    # Create new customization session with empty options
    new_session = CustomizationSession(
        product_id=session_data.product_id,
        template_id=session_data.template_id,
        session_key=session_key,
        options={},  # Start with empty options
        is_active=True
    )

    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    # Return response with session_id mapped from id
    return SessionResponse(
        session_id=new_session.id,
        session_key=new_session.session_key,
        product_id=new_session.product_id,
        template_id=new_session.template_id,
        options=new_session.options
    )
