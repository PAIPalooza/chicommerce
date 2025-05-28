from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

from app.core.config import settings
from .base_class import Base

# Create database engine
engine = create_engine(
    url=str(settings.DATABASE_URL),
    pool_pre_ping=True,
    echo=settings.LOG_LEVEL == "DEBUG",
    poolclass=NullPool,
)

# Create all tables
# Note: In a production environment, you would use Alembic for migrations
# This is just for development/testing purposes
def create_tables():
    Base.metadata.create_all(bind=engine)

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
