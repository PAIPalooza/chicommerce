"""
Template API endpoints.
"""
from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api import deps
from app.core.config import settings

router = APIRouter()


@router.get("/", response_model=List[schemas.Template])
async def read_templates(
    *,
    db: Session = Depends(deps.get_db_session),
    product_id: Optional[UUID] = Query(None, description="Filter by product ID")
) -> Any:
    """
    Retrieve templates, optionally filtered by product.
    
    Args:
        db: Database session
        product_id: Optional product UUID to filter by
        
    Returns:
        List of templates
    """
    if product_id:
        templates = crud.get_templates_by_product(db=db, product_id=product_id)
    else:
        # Return error - we require filtering by product
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product ID is required for listing templates",
        )
    return templates


@router.post("/", response_model=schemas.Template, status_code=status.HTTP_201_CREATED)
async def create_template(
    *,
    db: Session = Depends(deps.get_db_session),
    template_in: schemas.TemplateCreate,
    api_key: str = Depends(deps.get_admin_key)
) -> Any:
    """
    Create a new template for a product.
    
    - **product_id**: ID of the product this template belongs to
    - **version**: Template version number (must be unique per product)
    - **definition**: JSON schema defining the customization zones
    - **is_default**: Whether this template should be the default for the product
    - **customization_zones**: List of customization zones with their configurations
    
    Returns:
        The created template with all its details
    """
    # Check if product exists first
    product = crud.get_product(db=db, product_id=template_in.product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {template_in.product_id} not found",
        )
    
    try:
        # Create the template
        template = crud.create_template(db=db, template_in=template_in)
        return template
        
    except ValueError as e:
        # Handle validation errors from CRUD operations
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        # Log the unexpected error
        print(f"Unexpected error creating template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the template",
        )


@router.get("/{template_id}", response_model=schemas.Template)
async def read_template(
    *,
    db: Session = Depends(deps.get_db_session),
    template_id: UUID,
) -> Any:
    """
    Get template by ID.
    
    Args:
        db: Database session
        template_id: Template UUID
        
    Returns:
        Template
        
    Raises:
        HTTPException: If template not found
    """
    template = crud.get_template(db=db, template_id=template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )
    return template


@router.put("/{template_id}", response_model=schemas.Template)
async def update_template(
    *,
    db: Session = Depends(deps.get_db_session),
    template_id: UUID,
    template_in: schemas.TemplateUpdate,
    api_key: str = Depends(deps.get_admin_key)
) -> Any:
    """
    Update an existing template.
    
    - **version**: New version number (must be unique per product)
    - **definition**: Updated JSON schema defining the customization zones
    - **is_default**: Whether this template should be the default for the product
    - **customization_zones**: Updated list of customization zones
    
    Only the provided fields will be updated. All other fields remain unchanged.
    """
    try:
        # Check if template exists
        template = crud.get_template(db=db, template_id=template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template with ID {template_id} not found",
            )
        
        # Update the template
        template = crud.update_template(db=db, template=template, template_in=template_in)
        return template
        
    except ValueError as e:
        # Handle validation errors from CRUD operations
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        # Log the unexpected error
        print(f"Unexpected error updating template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while updating the template",
        )


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    *,
    db: Session = Depends(deps.get_db_session),
    template_id: UUID,
    api_key: str = Depends(deps.get_admin_key)
) -> None:
    """
    Delete a template.
    
    - If the template is marked as default, another template for the same product will be marked as default.
    - The last template for a product cannot be deleted.
    
    Returns:
        No content (204) on success
    """
    try:
        # Check if template exists
        template = crud.get_template(db=db, template_id=template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template with ID {template_id} not found",
            )
        
        # Delete the template
        if not crud.delete_template(db=db, template_id=template_id):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete template",
            )
            
        return None
        
    except ValueError as e:
        # Handle validation errors from CRUD operations
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        # Log the unexpected error
        print(f"Unexpected error deleting template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while deleting the template",
        )
