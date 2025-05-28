"""
Test script for Option Sets API endpoints.
"""
import sys
import os
import asyncio
import httpx
from uuid import uuid4
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_PRODUCT_ID = "dfe7a533-b82f-4579-ab4e-13ce93a0a5e6"  # Use an existing product ID
API_KEY = os.getenv("ADMIN_API_KEY", "dev-admin-api-key")  # Default to dev key if not set

async def test_option_sets():
    """Test the option sets endpoints."""
    async with httpx.AsyncClient() as client:
        # Create an option set
        create_data = {
            "name": "Size",
            "description": "T-Shirt Sizes",
            "is_required": True,
            "display_order": 1,
            "config": {"type": "dropdown"},
            "options": [
                {"name": "Small", "value": "S", "display_order": 1, "is_default": True},
                {"name": "Medium", "value": "M", "display_order": 2, "is_default": False},
                {"name": "Large", "value": "L", "display_order": 3, "is_default": False},
            ]
        }
        
        print("Creating option set with options...")
        response = await client.post(
            f"{BASE_URL}/option-sets/with-options/?product_id={TEST_PRODUCT_ID}",
            json=create_data,
            headers={"X-API-Key": API_KEY}
        )
        assert response.status_code == 201, f"Failed to create option set: {response.text}"
        option_set = response.json()
        option_set_id = option_set["id"]
        print(f"Created option set with ID: {option_set_id}")
        
        # Get the created option set
        print(f"Fetching option set {option_set_id}...")
        response = await client.get(
            f"{BASE_URL}/option-sets/{option_set_id}",
            headers={"X-API-Key": API_KEY}
        )
        assert response.status_code == 200, f"Failed to get option set: {response.text}"
        print(f"Fetched option set: {response.json()}")
        
        # List all option sets for the product
        print("Listing all option sets for the product...")
        response = await client.get(
            f"{BASE_URL}/option-sets/?product_id={TEST_PRODUCT_ID}",
            headers={"X-API-Key": API_KEY}
        )
        assert response.status_code == 200, f"Failed to list option sets: {response.text}"
        option_sets = response.json()
        print(f"Found {len(option_sets)} option sets")
        
        # Update the option set
        update_data = {
            "name": "T-Shirt Size",
            "description": "Available t-shirt sizes"
        }
        print(f"Updating option set {option_set_id}...")
        response = await client.put(
            f"{BASE_URL}/option-sets/{option_set_id}",
            json=update_data,
            headers={"X-API-Key": API_KEY}
        )
        assert response.status_code == 200, f"Failed to update option set: {response.text}"
        print(f"Updated option set: {response.json()}")
        
        # Add a new option to the option set
        new_option = {
            "name": "Extra Large",
            "value": "XL",
            "display_order": 4,
            "is_default": False,
            "additional_price": 200  # $2.00 extra
        }
        print(f"Adding new option to option set {option_set_id}...")
        response = await client.post(
            f"{BASE_URL}/option-sets/{option_set_id}/options/",
            json=new_option,
            headers={"X-API-Key": API_KEY}
        )
        assert response.status_code == 201, f"Failed to add option: {response.text}"
        new_option_data = response.json()
        option_id = new_option_data["id"]
        print(f"Added new option with ID: {option_id}")
        
        # List all options for the option set
        print(f"Listing all options for option set {option_set_id}...")
        response = await client.get(
            f"{BASE_URL}/option-sets/{option_set_id}/options/",
            headers={"X-API-Key": API_KEY}
        )
        assert response.status_code == 200, f"Failed to list options: {response.text}"
        options = response.json()
        print(f"Found {len(options)} options")
        
        # Delete the option
        print(f"Deleting option {option_id}...")
        response = await client.delete(
            f"{BASE_URL}/option-sets/options/{option_id}",
            headers={"X-API-Key": API_KEY}
        )
        assert response.status_code == 204, f"Failed to delete option: {response.text}"
        print(f"Deleted option {option_id}")
        
        # Delete the option set
        print(f"Deleting option set {option_set_id}...")
        response = await client.delete(
            f"{BASE_URL}/option-sets/{option_set_id}",
            headers={"X-API-Key": API_KEY}
        )
        assert response.status_code == 204, f"Failed to delete option set: {response.text}"
        print(f"Deleted option set {option_set_id}")
        
        print("All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_option_sets())
