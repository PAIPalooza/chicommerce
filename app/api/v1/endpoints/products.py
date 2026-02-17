"""
Product API endpoints using ZeroDB NoSQL.

This module has been migrated from PostgreSQL/SQLAlchemy to ZeroDB NoSQL.
Products are now stored in ZeroDB with denormalized template data.
"""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app import schemas
from app.api import deps
from app.services.product_service import ProductService

router = APIRouter()


@router.get("/", response_model=List[schemas.Product])
async def read_products(
    *,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    active_only: bool = Query(True, description="Filter for active products only")
) -> Any:
    """
    Retrieve products from ZeroDB.

    Args:
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        active_only: If True, returns only active products

    Returns:
        List of products
    """
    product_service = ProductService()
    products = await product_service.list_products(
        skip=skip,
        limit=limit,
        active_only=active_only
    )
    return products


@router.post("/", response_model=schemas.Product, status_code=status.HTTP_201_CREATED)
async def create_product(
    *,
    product_in: schemas.ProductCreate,
    api_key: str = Depends(deps.get_admin_key)
) -> Any:
    """
    Create new product in ZeroDB.

    Args:
        product_in: Product data
        api_key: Admin API key for authentication

    Returns:
        Created product
    """
    product_service = ProductService()
    product = await product_service.create_product(product_in)
    return product


@router.get("/{product_id}", response_model=schemas.ProductWithDefaultTemplate)
async def read_product(
    *,
    product_id: str,
) -> Any:
    """
    Get product by ID with its default template from ZeroDB.

    Args:
        product_id: Product UUID as string

    Returns:
        Product with default template

    Raises:
        HTTPException: If product not found
    """
    product_service = ProductService()
    try:
        product = await product_service.get_product_with_default_template(product_id)
        return product
    except HTTPException as e:
        if e.status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )
        raise


@router.put("/{product_id}", response_model=schemas.Product)
async def update_product(
    *,
    product_id: str,
    product_in: schemas.ProductUpdate,
    api_key: str = Depends(deps.get_admin_key)
) -> Any:
    """
    Update a product in ZeroDB.

    Args:
        product_id: Product UUID as string
        product_in: Product update data
        api_key: Admin API key for authentication

    Returns:
        Updated product

    Raises:
        HTTPException: If product not found
    """
    product_service = ProductService()
    try:
        product = await product_service.update_product(product_id, product_in)
        return product
    except HTTPException as e:
        if e.status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )
        raise


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    *,
    product_id: str,
    api_key: str = Depends(deps.get_admin_key)
) -> None:
    """
    Delete a product from ZeroDB.

    Args:
        product_id: Product UUID as string
        api_key: Admin API key for authentication

    Raises:
        HTTPException: If product not found or deletion fails
    """
    product_service = ProductService()
    try:
        await product_service.delete_product(product_id, cascade=True)
    except HTTPException as e:
        if e.status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )
        raise
    except ValueError as e:
        # Handle validation errors from service operations
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        # Log the full error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error deleting product {product_id}: {str(e)}", exc_info=True)

        # Return a more specific error message
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete product: {str(e)}",
        )
