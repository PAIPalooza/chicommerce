"""Test script for cart functionality."""
import asyncio
import os
import uuid
from typing import Dict, Any
from uuid import UUID

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "test-admin-key")  # Get from environment or use default

# Test data
TEST_PRODUCT = {
    "name": "Test T-Shirt",
    "description": "A test t-shirt for cart testing",
    "base_price": 29.99,
    "is_active": True
}

TEST_OPTION_SET = {
    "name": "Size",
    "description": "T-Shirt Sizes",
    "is_required": True,
    "display_order": 1,
    "config": {"type": "dropdown"},
    "options": [
        {
            "name": "Small",
            "value": "S",
            "display_order": 1,
            "additional_price": 0,
            "is_default": True,
            "config": {}
        },
        {
            "name": "Medium",
            "value": "M",
            "display_order": 2,
            "additional_price": 0,
            "is_default": False,
            "config": {}
        },
        {
            "name": "Large",
            "value": "L",
            "display_order": 3,
            "additional_price": 0,
            "is_default": False,
            "config": {}
        }
    ]
}

class TestClient:
    """Test client for making HTTP requests."""
    
    def __init__(self, base_url: str, session_id: str = None):
        self.base_url = base_url
        self.session_id = session_id
        self.client = httpx.AsyncClient()
        self.headers = {}
        if self.session_id:
            self.headers["Cookie"] = f"session_id={self.session_id}"
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def get(self, path: str, **kwargs):
        """Make a GET request."""
        return await self.client.get(
            f"{self.base_url}{path}",
            headers=self.headers,
            **kwargs
        )
    
    async def post(self, path: str, json: Dict[str, Any] = None, **kwargs):
        """Make a POST request."""
        return await self.client.post(
            f"{self.base_url}{path}",
            json=json,
            headers=self.headers,
            **kwargs
        )
    
    async def put(self, path: str, json: Dict[str, Any] = None, **kwargs):
        """Make a PUT request."""
        return await self.client.put(
            f"{self.base_url}{path}",
            json=json,
            headers=self.headers,
            **kwargs
        )
    
    async def delete(self, path: str, **kwargs):
        """Make a DELETE request."""
        return await self.client.delete(
            f"{self.base_url}{path}",
            headers=self.headers,
            **kwargs
        )


async def test_cart_workflow():
    """Test the complete cart workflow."""
    # Create a test client with a new session
    client = TestClient(BASE_URL)
    
    try:
        # Step 1: Get or create a cart (should create a new one)
        print("1. Getting or creating a cart...")
        response = await client.get("/cart")
        assert response.status_code == 200, f"Failed to get cart: {response.text}"
        cart = response.json()
        print(f"Cart created with ID: {cart['id']}")
        
        # Store the session ID for future requests
        session_id = response.cookies.get("session_id")
        if session_id:
            client.session_id = session_id
            client.headers["Cookie"] = f"session_id={session_id}"
        
        # Step 2: Create a test product (admin operation)
        print("\n2. Creating a test product...")
        admin_client = TestClient(BASE_URL)
        admin_client.headers["X-API-Key"] = ADMIN_API_KEY
        
        response = await admin_client.post(
            "/products/",
            json=TEST_PRODUCT
        )
        assert response.status_code == 201, f"Failed to create product: {response.text}"
        product = response.json()
        print(f"Created product with ID: {product['id']}")
        
        # Step 3: Create an option set for the product (admin operation)
        print("\n3. Creating an option set for the product...")
        response = await admin_client.post(
            f"/option-sets/with-options/",
            params={"product_id": str(product['id'])},
            json=TEST_OPTION_SET
        )
        assert response.status_code == 201, f"Failed to create option set: {response.text}"
        option_set = response.json()
        print(f"Created option set with ID: {option_set['id']}")
        
        # Step 4: Start a customization session
        print("\n4. Starting a customization session...")
        customization_data = {
            "product_id": str(product["id"]),
            "session_id": str(session_id),
            "customization_data": {
                "size": "M",
                "color": "blue"
            }
        }
        response = await client.post(
            "/customization-sessions",
            json=customization_data
        )
        assert response.status_code == 200, f"Failed to create customization session: {response.text}"
        session = response.json()
        print(f"Created customization session with ID: {session['id']}")
        
        # Step 5: Add item to cart
        print("\n5. Adding item to cart...")
        cart_item = {
            "product_id": product["id"],
            "quantity": 2,
            "unit_price": float(product["base_price"]),  # Ensure it's a float
            "customization_data": session["customization_data"]
        }
        response = await client.post("/cart/items", json=cart_item)
        assert response.status_code == 201, f"Failed to add item to cart: {response.text}"
        updated_cart = response.json()
        print(f"Added item to cart. Cart now has {updated_cart['total_items']} items.")
        
        # Step 6: Verify cart contents
        print("\n6. Verifying cart contents...")
        response = await client.get("/cart")
        assert response.status_code == 200, f"Failed to get cart: {response.text}"
        cart = response.json()
        assert len(cart["items"]) == 1, f"Expected 1 item in cart, got {len(cart['items'])}"
        assert cart["items"][0]["product_id"] == str(product["id"]), "Product ID mismatch"
        assert cart["items"][0]["quantity"] == 2, "Quantity mismatch"
        # Convert both to float to ensure consistent comparison
        assert float(cart["items"][0]["unit_price"]) == float(product["base_price"]), \
            f"Price mismatch: {cart['items'][0]['unit_price']} != {product['base_price']}"
        print("Cart verification passed!")
        
        # Step 7: Update cart item quantity
        print("\n7. Updating cart item quantity...")
        item_id = cart["items"][0]["id"]
        response = await client.put(
            f"/cart/items/{item_id}",
            json={"quantity": 3}
        )
        assert response.status_code == 200, f"Failed to update cart item: {response.text}"
        updated_cart = response.json()
        assert updated_cart["items"][0]["quantity"] == 3, "Failed to update quantity"
        print(f"Updated item quantity to 3. Cart now has {updated_cart['total_items']} items.")
        
        # Step 8: Remove item from cart
        print("\n8. Removing item from cart...")
        response = await client.delete(f"/cart/items/{item_id}")
        assert response.status_code == 200, f"Failed to remove item from cart: {response.text}"
        updated_cart = response.json()
        assert len(updated_cart["items"]) == 0, "Cart should be empty after removing the only item"
        print("Item removed from cart. Cart is now empty.")
        
        # Clean up test data
        print("\n9. Cleaning up test data...")
        try:
            # First, get the cart to clear any items
            cart_response = await client.get("/cart")
            if cart_response.status_code == 200:
                cart = cart_response.json()
                # Remove all items from the cart
                for item in cart.get("items", []):
                    await client.delete(f"/cart/items/{item['id']}")
            
            # Clean up active customization sessions for the product
            try:
                # In a real app, we would use an API endpoint to list and close sessions
                # For testing, we'll use direct DB access
                import sys
                from pathlib import Path
                # Add the project root to the Python path
                project_root = str(Path(__file__).parent.parent)
                if project_root not in sys.path:
                    sys.path.append(project_root)
                
                from app.db.session import SessionLocal
                from app.models.cart import CustomizationSession
                
                db = SessionLocal()
                try:
                    # Close all active sessions for this product
                    db.query(CustomizationSession).filter(
                        CustomizationSession.product_id == product['id'],
                        CustomizationSession.is_active == True
                    ).update({"is_active": False}, synchronize_session=False)
                    db.commit()
                    print(f"Closed active customization sessions for product {product['id']}")
                except Exception as e:
                    print(f"Warning: Error closing customization sessions: {str(e)}")
                    db.rollback()
                finally:
                    db.close()
            except Exception as e:
                print(f"Warning: Failed to close customization sessions: {str(e)}")
            
            # Try to delete the option set
            try:
                # First, delete all options in the option set
                response = await admin_client.get(f"/option-sets/{option_set['id']}/options")
                if response.status_code == 200:
                    for option in response.json():
                        await admin_client.delete(f"/option-sets/options/{option['id']}")
                
                # Then delete the option set itself
                response = await admin_client.delete(f"/option-sets/{option_set['id']}")
                if response.status_code not in [200, 204]:
                    print(f"Warning: Failed to delete option set: {response.status_code} - {response.text}")
                else:
                    print("Deleted option set successfully")
            except Exception as e:
                print(f"Warning: Error deleting option set: {str(e)}")
            
            # Try to delete the product
            try:
                response = await admin_client.delete(f"/products/{product['id']}")
                if response.status_code not in [200, 204]:
                    print(f"Warning: Failed to delete product: {response.status_code} - {response.text}")
                else:
                    print("Deleted product successfully")
            except Exception as e:
                print(f"Warning: Error deleting product: {str(e)}")
            
            print("Test cleanup completed. Some resources may not have been fully cleaned up.")
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")
            raise  # Re-raise to fail the test
        
        print("\n✅ All tests passed!")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    finally:
        # Clean up
        await client.close()
        if 'admin_client' in locals():
            await admin_client.close()

if __name__ == "__main__":
    asyncio.run(test_cart_workflow())
