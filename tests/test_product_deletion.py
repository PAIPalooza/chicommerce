"""
Tests for product deletion functionality.
"""
import pytest
from fastapi import status
from sqlalchemy.orm import Session

from app.models.cart import Cart, CartItem, CustomizationSession
from app.models.product import Product

@pytest.mark.asyncio
async def test_delete_product_success(
    client,
    db_session: Session,
    sample_product: Product,
):
    """Test successful product deletion."""
    # Delete the product
    response = client.delete(
        f"/api/v1/products/{sample_product.id}",
        headers={"X-API-Key": "test-admin-key"}
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify the product is deleted
    response = client.get(f"/api/v1/products/{sample_product.id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_delete_product_with_cart_items(
    client,
    db_session: Session,
    sample_product: Product,
):
    """Test deleting a product that has items in a cart."""
    # Create a cart and add the product to it
    cart = Cart(session_id="test-session")
    db_session.add(cart)
    db_session.flush()
    
    cart_item = CartItem(
        cart_id=cart.id,
        product_id=sample_product.id,
        quantity=1,
        unit_price=99.99,
        customization_data={"size": "M"}
    )
    db_session.add(cart_item)
    db_session.commit()
    
    # Attempt to delete the product
    response = client.delete(
        f"/api/v1/products/{sample_product.id}",
        headers={"X-API-Key": "test-admin-key"}
    )
    
    # Should fail with 400 Bad Request
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "cart items" in response.json()["detail"].lower()
    
    # Verify the product still exists
    response = client.get(f"/api/v1/products/{sample_product.id}")
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.asyncio
async def test_delete_product_with_customization_sessions(
    client,
    db_session: Session,
    sample_product: Product,
):
    """Test deleting a product with customization sessions."""
    # Create a customization session for the product
    session = CustomizationSession(
        session_id="test-session",
        product_id=sample_product.id,
        customization_data={"size": "M", "color": "blue"},
        is_active=True
    )
    db_session.add(session)
    db_session.commit()
    
    # Delete the product (should succeed as we now handle sessions)
    response = client.delete(
        f"/api/v1/products/{sample_product.id}",
        headers={"X-API-Key": "test-admin-key"}
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify the product is deleted
    response = client.get(f"/api/v1/products/{sample_product.id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_delete_nonexistent_product(
    client,
    db_session: Session,
):
    """Test deleting a product that doesn't exist."""
    non_existent_id = "00000000-0000-0000-0000-000000000000"
    response = client.delete(
        f"/api/v1/products/{non_existent_id}",
        headers={"X-API-Key": "test-admin-key"}
    )
    # Expect 404 Not Found when trying to delete a non-existent product
    assert response.status_code == status.HTTP_404_NOT_FOUND
