from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from sqlalchemy.pool import NullPool

from app.core.config import settings

# SQLAlchemy 2.0 declarative base
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass

# Create database engine
engine = create_engine(
    url=str(settings.DATABASE_URL),
    pool_pre_ping=True,
    echo=settings.LOG_LEVEL == "DEBUG",
    poolclass=NullPool,
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)

def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting DB session.
    
    Yields:
        Session: Database session
    
    Example:
        ```python
        def some_endpoint(db: Session = Depends(get_db)):
            # Use the database session
            items = db.query(Item).all()
            return items
        ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
