"""
Test configuration for pytest fixtures.
"""
import os
import pytest
from typing import Dict, Generator, Any

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import NullPool

from app.main import app
from app.api import deps
from app.db.session import Base
from app.core.config import settings

# Test database URL from settings
TEST_DATABASE_URL = settings.TEST_DATABASE_URL

@pytest.fixture(scope="session")
def test_db_engine():
    """
    Create a test database engine.
    
    This fixture creates a fresh test database for each test session and drops it
    when the tests are done. It uses SQLAlchemy 2.0 style.
    """
    # Create a test database if it doesn't exist
    db_url = str(TEST_DATABASE_URL)
    
    # Connect to the default postgres database to create our test database
    default_db_url = db_url.replace("/chicommerce_test", "/postgres")
    default_engine = create_engine(
        default_db_url,
        isolation_level="AUTOCOMMIT",
        poolclass=NullPool,
    )
    
    # Create test database if it doesn't exist
    with default_engine.connect() as conn:
        # End any open transaction
        conn.execute(text("COMMIT"))
        # Drop the test database if it exists
        conn.execute(text("DROP DATABASE IF EXISTS chicommerce_test"))
        # Create a fresh test database
        conn.execute(text("CREATE DATABASE chicommerce_test"))
    
    # Now connect to the test database
    engine = create_engine(
        db_url,
        poolclass=NullPool,
        echo=bool(os.getenv("SQL_ECHO", "").lower() == "true"),
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup - close all connections and drop the test database
    engine.dispose()
    
    # Connect back to the default database to drop the test database
    with default_engine.connect() as conn:
        # End any open transaction
        conn.execute(text("COMMIT"))
        
        # Disconnect all other connections to the test database
        # This needs to be in a separate execution context
        with conn.connection.cursor() as cur:
            cur.execute("""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = 'chicommerce_test'
                AND pid <> pg_backend_pid();
            """)
        
        # Commit the termination of other connections
        conn.execute(text("COMMIT"))
        
        # Drop the database in a new transaction
        with conn.connection.cursor() as cur:
            cur.execute("DROP DATABASE IF EXISTS chicommerce_test")
            # Commit the DROP DATABASE command
            conn.connection.commit()
    
    default_engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_db_engine) -> Generator[Session, None, None]:
    """
    Creates a fresh database session for each test.
    """
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_db_engine
    )
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture(scope="function")
def client(db_session) -> Generator[TestClient, None, None]:
    """
    Create a test client with overridden dependencies.
    """
    def _get_test_db():
        try:
            yield db_session
        finally:
            pass
    
    def _get_admin_key():
        return "test-admin-key"
    
    app.dependency_overrides[deps.get_db_session] = _get_test_db
    app.dependency_overrides[deps.get_admin_key] = _get_admin_key
    
    with TestClient(app) as c:
        yield c
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def sample_product_data() -> Dict[str, Any]:
    """
    Sample product data for tests.
    """
    return {
        "name": "Test Product",
        "description": "A test product for unit tests",
        "base_price": 19.99,
        "media": {"images": ["test-image.jpg"]},
        "is_active": True
    }


@pytest.fixture(scope="function")
def sample_template_data(sample_product_id) -> Dict[str, Any]:
    """
    Sample template data for tests.
    """
    return {
        "product_id": sample_product_id,
        "version": 1,
        "definition": {
            "zones": {
                "text_front": {"type": "text", "max_length": 50},
                "image_front": {"type": "image", "formats": ["jpg", "png"]}
            }
        },
        "is_default": True,
        "customization_zones": [
            {
                "key": "text_front",
                "type": "text",
                "config": {"max_length": 50},
                "order_index": 0
            },
            {
                "key": "image_front",
                "type": "image",
                "config": {"formats": ["jpg", "png"]},
                "order_index": 1
            }
        ]
    }
