"""
API endpoints for managing option sets.
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from uuid import UUID

from app import models, schemas
from app.api.deps import get_db_session, get_admin_key
from app.crud.option_set import (
    create_option_set as crud_create_option_set,
    get_option_set as crud_get_option_set,
    get_option_sets_by_product as crud_get_option_sets_by_product,
    update_option_set as crud_update_option_set,
    delete_option_set as crud_delete_option_set,
    create_option as crud_create_option,
    get_option as crud_get_option,
    get_options_by_option_set as crud_get_options_by_option_set,
    update_option as crud_update_option,
    delete_option as crud_delete_option,
    create_option_set_with_options as crud_create_option_set_with_options
)
from app.crud.product import get_product as crud_get_product
from app.schemas.option_set import (
    OptionSet,
    OptionSetCreate,
    OptionSetUpdate,
    OptionSetWithOptionsCreate,
    OptionSetWithProduct
)
from app.schemas.option import Option, OptionCreate, OptionUpdate

router = APIRouter()


@router.get("/", response_model=List[OptionSetWithProduct])
def get_option_sets(
    product_id: UUID,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db_session),
    api_key: str = Depends(get_admin_key),
) -> List[OptionSetWithProduct]:
    """
    Get all option sets for a product.
    """
    # Check if product exists
    db_product = crud_get_product(db, product_id)
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    
    option_sets = crud_get_option_sets_by_product(
        db, product_id=product_id, skip=skip, limit=limit, active_only=active_only
    )
    
    # Convert each option set to include product_name
    result = []
    for option_set in option_sets:
        option_set_data = option_set.__dict__
        option_set_data["product_name"] = option_set.product.name
        result.append(OptionSetWithProduct(**option_set_data))
    
    return result


@router.post("/", response_model=OptionSet, status_code=status.HTTP_201_CREATED)
def create_option_set(
    product_id: UUID,
    option_set_in: OptionSetCreate,
    db: Session = Depends(get_db_session),
    api_key: str = Depends(get_admin_key),
) -> OptionSet:
    """
    Create a new option set for a product.
    """
    # Check if product exists
    db_product = crud_get_product(db, product_id)
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    
    return crud_create_option_set(
        db, option_set_in=option_set_in, product_id=product_id
    )


@router.post("/with-options/", response_model=OptionSet, status_code=status.HTTP_201_CREATED)
def create_option_set_with_options(
    product_id: UUID,
    option_set_in: OptionSetWithOptionsCreate,
    db: Session = Depends(get_db_session),
    api_key: str = Depends(get_admin_key),
) -> OptionSet:
    """
    Create a new option set with options in a single request.
    """
    # Check if product exists
    db_product = crud_get_product(db, product_id)
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    
    # Create the option set with options
    return crud_create_option_set_with_options(
        db, option_set_in=option_set_in, product_id=product_id
    )


@router.get("/{option_set_id}", response_model=OptionSetWithProduct)
def read_option_set(
    option_set_id: UUID,
    db: Session = Depends(get_db_session),
    api_key: str = Depends(get_admin_key),
) -> OptionSetWithProduct:
    """
    Get an option set by ID.
    """
    option_set = crud_get_option_set(db, option_set_id=option_set_id)
    if not option_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Option set with ID {option_set_id} not found"
        )
    
    # Convert to dict to add product name
    option_set_data = option_set.__dict__
    option_set_data["product_name"] = option_set.product.name
    return OptionSetWithProduct(**option_set_data)


@router.put("/{option_set_id}", response_model=OptionSet)
def update_option_set(
    option_set_id: UUID,
    option_set_in: OptionSetUpdate,
    db: Session = Depends(get_db_session),
    api_key: str = Depends(get_admin_key),
) -> OptionSet:
    """
    Update an option set.
    """
    db_option_set = crud_get_option_set(db, option_set_id=option_set_id)
    if not db_option_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Option set with ID {option_set_id} not found"
        )
    
    return crud_update_option_set(
        db, db_option_set=db_option_set, option_set_in=option_set_in
    )


@router.delete("/{option_set_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_option_set(
    option_set_id: UUID,
    db: Session = Depends(get_db_session),
    api_key: str = Depends(get_admin_key),
) -> None:
    """
    Delete an option set.
    """
    db_option_set = crud_get_option_set(db, option_set_id=option_set_id)
    if not db_option_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Option set with ID {option_set_id} not found"
        )
    
    crud_delete_option_set(db, option_set_id=option_set_id)
    return None


# Options endpoints
@router.get("/{option_set_id}/options/", response_model=List[Option])
def read_options(
    option_set_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_session),
    api_key: str = Depends(get_admin_key),
) -> List[Option]:
    """
    Get options for an option set.
    """
    # Check if option set exists
    db_option_set = crud_get_option_set(db, option_set_id=option_set_id)
    if not db_option_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Option set with ID {option_set_id} not found"
        )
    
    return crud_get_options_by_option_set(
        db, option_set_id=option_set_id, skip=skip, limit=limit
    )


@router.post("/{option_set_id}/options/", response_model=Option, status_code=status.HTTP_201_CREATED)
def create_option(
    option_set_id: UUID,
    option_in: OptionCreate,
    db: Session = Depends(get_db_session),
    api_key: str = Depends(get_admin_key),
) -> Option:
    """
    Create a new option for an option set.
    """
    # Check if option set exists
    db_option_set = crud_get_option_set(db, option_set_id=option_set_id)
    if not db_option_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Option set with ID {option_set_id} not found"
        )
    
    return crud_create_option(
        db, option_in=option_in, option_set_id=option_set_id
    )


@router.get("/options/{option_id}", response_model=Option)
def read_option(
    option_id: UUID,
    db: Session = Depends(get_db_session),
    api_key: str = Depends(get_admin_key),
) -> Option:
    """
    Get an option by ID.
    """
    option = crud_get_option(db, option_id=option_id)
    if not option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Option with ID {option_id} not found"
        )
    return option


@router.put("/options/{option_id}", response_model=Option)
def update_option(
    option_id: UUID,
    option_in: OptionUpdate,
    db: Session = Depends(get_db_session),
    api_key: str = Depends(get_admin_key),
) -> Option:
    """
    Update an option.
    """
    db_option = crud_get_option(db, option_id=option_id)
    if not db_option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Option with ID {option_id} not found"
        )
    
    return crud_update_option(
        db, db_option=db_option, option_in=option_in
    )


@router.delete("/options/{option_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_option(
    option_id: UUID,
    db: Session = Depends(get_db_session),
    api_key: str = Depends(get_admin_key),
) -> None:
    """
    Delete an option.
    """
    db_option = crud_get_option(db, option_id=option_id)
    if not db_option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Option with ID {option_id} not found"
        )
    
    crud_delete_option(db, option_id=option_id)
    return None
