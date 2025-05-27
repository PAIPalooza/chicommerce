"""
Script to create test data for the ChiCommerce API.
"""
import json
from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.product import Product
from app.models.template import Template


def create_test_data():
    """Create test product and template data."""
    db = SessionLocal()
    
    try:
        # Create a test product
        product = Product(
            id=uuid4(),
            name="Test T-Shirt",
            description="A test t-shirt product",
            base_price=29.99,
            media={"images": ["image1.jpg", "image2.jpg"]},
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(product)
        
        # Create a default template for the product
        template = Template(
            id=uuid4(),
            product_id=product.id,
            version=1,
            definition={
                "name": "Default T-Shirt Template",
                "description": "Default template for t-shirt customization",
                "zones": [
                    {
                        "id": "front",
                        "name": "Front",
                        "type": "image",
                        "required": True,
                        "max_size_mb": 5,
                        "allowed_types": ["image/png", "image/jpeg"],
                        "dimensions": {"width": 1000, "height": 1000},
                        "position": {"x": 0, "y": 0, "z": 0}
                    }
                ]
            },
            is_default=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(template)
        
        db.commit()
        
        print(f"Created test product with ID: {product.id}")
        print(f"Created default template with ID: {template.id}")
        
        return {"product_id": str(product.id), "template_id": str(template.id)}
        
    except Exception as e:
        db.rollback()
        print(f"Error creating test data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_test_data()
