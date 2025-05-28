"""
Product API endpoints.
"""
from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api import deps
from app.core.config import settings

router = APIRouter()


@router.get("/", response_model=List[schemas.Product])
async def read_products(
    *,
    db: Session = Depends(deps.get_db_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    active_only: bool = Query(True, description="Filter for active products only")
) -> Any:
    """
    Retrieve products.
    
    Args:
        db: Database session
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        active_only: If True, returns only active products
        
    Returns:
        List of products
    """
    products = crud.get_products(db=db, skip=skip, limit=limit, active_only=active_only)
    return products


@router.post("/", response_model=schemas.Product, status_code=status.HTTP_201_CREATED)
async def create_product(
    *,
    db: Session = Depends(deps.get_db_session),
    product_in: schemas.ProductCreate,
    api_key: str = Depends(deps.get_admin_key)
) -> Any:
    """
    Create new product.
    
    Args:
        db: Database session
        product_in: Product data
        api_key: Admin API key for authentication
        
    Returns:
        Created product
    """
    product = crud.create_product(db=db, product_in=product_in)
    return product


@router.get("/{product_id}", response_model=schemas.ProductWithDefaultTemplate)
async def read_product(
    *,
    db: Session = Depends(deps.get_db_session),
    product_id: UUID,
) -> Any:
    """
    Get product by ID with its default template.
    
    Args:
        db: Database session
        product_id: Product UUID
        
    Returns:
        Product with default template
        
    Raises:
        HTTPException: If product not found
    """
    product = crud.get_product_with_default_template(db=db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return product


@router.put("/{product_id}", response_model=schemas.Product)
async def update_product(
    *,
    db: Session = Depends(deps.get_db_session),
    product_id: UUID,
    product_in: schemas.ProductUpdate,
    api_key: str = Depends(deps.get_admin_key)
) -> Any:
    """
    Update a product.
    
    Args:
        db: Database session
        product_id: Product UUID
        product_in: Product update data
        api_key: Admin API key for authentication
        
    Returns:
        Updated product
        
    Raises:
        HTTPException: If product not found
    """
    product = crud.get_product(db=db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    product = crud.update_product(db=db, product=product, product_in=product_in)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    *,
    db: Session = Depends(deps.get_db_session),
    product_id: UUID,
    api_key: str = Depends(deps.get_admin_key)
) -> None:
    """
    Delete a product.
    
    Args:
        db: Database session
        product_id: Product UUID
        api_key: Admin API key for authentication
        
    Raises:
        HTTPException: If product not found or deletion fails
    """
    try:
        product_exists = crud.delete_product(db=db, product_id=product_id)
        if not product_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except ValueError as e:
        # Handle validation errors from CRUD operations
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        # Log the full error for debugging
        print(f"Error deleting product {product_id}: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        
        # Return a more specific error message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete product: {str(e)}",
        )
