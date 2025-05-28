"""Base class for SQLAlchemy models."""
from typing import Any

from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    """Base class for all database models."""
    
    # Generate __tablename__ automatically
    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Generate table name automatically from class name.
        
        Converts CamelCase class name to snake_case table name.
        """
        return ''.join(
            ['_' + i.lower() if i.isupper() else i 
             for i in cls.__name__]).lstrip('_')
    
    def __repr__(self) -> str:
        """String representation of the model instance."""
        return f"<{self.__class__.__name__} {self.id}>"
