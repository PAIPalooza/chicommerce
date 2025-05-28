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
    
    # Store the original dependencies
    original_get_db = app.dependency_overrides.get(deps.get_db_session, deps.get_db_session)
    original_get_admin_key = app.dependency_overrides.get(deps.get_admin_key, deps.get_admin_key)
    
    # Set up test dependencies
    app.dependency_overrides[deps.get_db_session] = _get_test_db
    
    # Create a test client
    client = TestClient(app)
    
    # Add a method to set authentication
    def set_auth(api_key: str = None):
        if api_key is None:
            # Remove the admin key override to test authentication
            if deps.get_admin_key in app.dependency_overrides:
                del app.dependency_overrides[deps.get_admin_key]
        else:
            # Set a specific API key for testing
            def _get_test_admin_key():
                return api_key
            app.dependency_overrides[deps.get_admin_key] = _get_test_admin_key
        return client
    
    # Set default auth for backward compatibility
    client.set_auth = set_auth
    client.set_auth("test-admin-key")
    
    try:
        yield client
    finally:
        # Clean up
        app.dependency_overrides.clear()
        # Restore original overrides
        if original_get_db != deps.get_db_session:
            app.dependency_overrides[deps.get_db_session] = original_get_db
        if original_get_admin_key != deps.get_admin_key:
            app.dependency_overrides[deps.get_admin_key] = original_get_admin_key


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
def sample_product(db_session: Session, sample_product_data: Dict[str, Any]) -> Any:
    """
    Create a sample product in the database.
    """
    from app.models.product import Product
    
    product = Product(**sample_product_data)
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture(scope="function")
def sample_product_id(sample_product: Any) -> str:
    """
    Return the ID of the sample product.
    """
    return sample_product.id


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


@pytest.fixture(scope="function")
def sample_template(db_session: Session, sample_product_id: str) -> Any:
    """
    Create a sample template in the database.
    """
    from app.models.template import Template, CustomizationZone
    
    template = Template(
        product_id=sample_product_id,
        version=1,
        definition={
            "zones": {
                "text_1": {"type": "text", "max_length": 100},
                "image_1": {"type": "image", "formats": ["png", "jpg"]}
            }
        },
        is_default=True
    )
    
    db_session.add(template)
    db_session.flush()  # Flush to get the template ID
    
    # Add customization zones
    zones = [
        CustomizationZone(
            template_id=template.id,
            key="text_1",
            type="text",
            config={"max_length": 100},
            order_index=0
        ),
        CustomizationZone(
            template_id=template.id,
            key="image_1",
            type="image",
            config={"formats": ["png", "jpg"]},
            order_index=1
        )
    ]
    
    db_session.add_all(zones)
    db_session.commit()
    db_session.refresh(template)
    return template
