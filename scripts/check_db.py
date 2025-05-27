"""Script to check database connection and query data."""
from app.db.session import SessionLocal, engine
from app.models.product import Product
from app.models.template import Template

def check_database():
    """Check database connection and query test data."""
    db = SessionLocal()
    try:
        # Check products
        products = db.query(Product).all()
        print(f"Found {len(products)} products:")
        for product in products:
            print(f"- {product.name} (ID: {product.id})")
        
        # Check templates
        templates = db.query(Template).all()
        print(f"\nFound {len(templates)} templates:")
        for template in templates:
            print(f"- Template for product {template.product_id} (Version: {template.version}, Default: {template.is_default})")
        
        # Try the get_product_with_default_template function
        if products:
            product_id = products[0].id
            print(f"\nTesting get_product_with_default_template for product ID: {product_id}")
            from app.crud import product as crud_product
            result = crud_product.get_product_with_default_template(db, product_id)
            print(f"Result: {result}")
            
    except Exception as e:
        print(f"Error querying database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_database()
