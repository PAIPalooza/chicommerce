"""
CRUD operations for OptionSet and Option models.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.option_set import OptionSet, Option
from app.schemas.option_set import OptionSetCreate, OptionSetUpdate, OptionSetWithOptionsCreate
from app.schemas.option import OptionCreate, OptionUpdate


def get_option_set(db: Session, option_set_id: UUID) -> Optional[OptionSet]:
    """Get an option set by ID."""
    return db.query(OptionSet).filter(OptionSet.id == option_set_id).first()


def get_option_sets_by_product(
    db: Session, 
    product_id: UUID, 
    skip: int = 0, 
    limit: int = 100,
    active_only: bool = True
) -> List[OptionSet]:
    """Get all option sets for a product."""
    query = db.query(OptionSet).filter(OptionSet.product_id == product_id)
    if active_only:
        query = query.filter(OptionSet.is_active == True)
    return query.offset(skip).limit(limit).all()


def create_option_set(
    db: Session, 
    option_set_in: OptionSetCreate, 
    product_id: UUID
) -> OptionSet:
    """Create a new option set for a product."""
    db_option_set = OptionSet(
        **option_set_in.dict(exclude={"options"}),
        product_id=product_id
    )
    db.add(db_option_set)
    db.commit()
    db.refresh(db_option_set)
    return db_option_set


def update_option_set(
    db: Session, 
    db_option_set: OptionSet, 
    option_set_in: OptionSetUpdate
) -> OptionSet:
    """Update an existing option set."""
    update_data = option_set_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_option_set, field, value)
    db.commit()
    db.refresh(db_option_set)
    return db_option_set


def delete_option_set(db: Session, option_set_id: UUID) -> bool:
    """Delete an option set by ID."""
    db_option_set = get_option_set(db, option_set_id)
    if not db_option_set:
        return False
    db.delete(db_option_set)
    db.commit()
    return True


def get_option(db: Session, option_id: UUID) -> Optional[Option]:
    """Get an option by ID."""
    return db.query(Option).filter(Option.id == option_id).first()


def get_options_by_option_set(
    db: Session, 
    option_set_id: UUID, 
    skip: int = 0, 
    limit: int = 100
) -> List[Option]:
    """Get all options for an option set."""
    return (
        db.query(Option)
        .filter(Option.option_set_id == option_set_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_option(
    db: Session, 
    option_in: OptionCreate, 
    option_set_id: UUID
) -> Option:
    """Create a new option for an option set."""
    db_option = Option(
        **option_in.dict(),
        option_set_id=option_set_id
    )
    db.add(db_option)
    db.commit()
    db.refresh(db_option)
    return db_option


def update_option(
    db: Session, 
    db_option: Option, 
    option_in: OptionUpdate
) -> Option:
    """Update an existing option."""
    update_data = option_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_option, field, value)
    db.commit()
    db.refresh(db_option)
    return db_option


def delete_option(db: Session, option_id: UUID) -> bool:
    """Delete an option by ID."""
    db_option = get_option(db, option_id)
    if not db_option:
        return False
    db.delete(db_option)
    db.commit()
    return True


def create_option_set_with_options(
    db: Session, 
    option_set_in: OptionSetWithOptionsCreate, 
    product_id: UUID
) -> OptionSet:
    """Create an option set with its options in a single transaction."""
    # Create the option set
    db_option_set = OptionSet(
        **option_set_in.dict(exclude={"options"}),
        product_id=product_id
    )
    db.add(db_option_set)
    db.flush()  # Flush to get the ID without committing
    
    # Create options
    for option_in in option_set_in.options:
        db_option = Option(
            **option_in.dict(),
            option_set_id=db_option_set.id
        )
        db.add(db_option)
    
    db.commit()
    db.refresh(db_option_set)
    return db_option_set
