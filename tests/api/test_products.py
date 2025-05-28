"""
Integration tests for Product API endpoints.
"""
import pytest
import json
from uuid import uuid4, UUID
from fastapi import status

from app.models.product import Product


class TestProductsAPI:
    """
    Test suite for Product API endpoints.
    
    Following BDD pattern with descriptive test method names.
    """
    
    def test_get_products_returns_active_products_only(self, client, db_session, sample_product_data):
        """
        GIVEN two products, one active and one inactive
        WHEN the GET /products endpoint is called with active_only=true
        THEN only the active product should be returned
        """
        # Arrange
        active_product = Product(**sample_product_data)
        inactive_product = Product(
            name="Inactive Product",
            description="An inactive product",
            base_price=9.99,
            is_active=False
        )
        db_session.add(active_product)
        db_session.add(inactive_product)
        db_session.commit()
        
        # Act
        response = client.get("/api/v1/products/?active_only=true")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Product"
        assert data[0]["is_active"] is True
    
    def test_get_products_returns_all_products_when_active_only_false(self, client, db_session, sample_product_data):
        """
        GIVEN two products, one active and one inactive
        WHEN the GET /products endpoint is called with active_only=false
        THEN both products should be returned
        """
        # Arrange - Clean up any existing products first
        db_session.query(Product).delete()
        db_session.commit()
        
        # Create our test products
        active_product = Product(**sample_product_data)
        inactive_product = Product(
            name="Inactive Product",
            description="An inactive product",
            base_price=9.99,
            is_active=False
        )
        db_session.add(active_product)
        db_session.add(inactive_product)
        db_session.commit()
        
        # Act
        response = client.get("/api/v1/products/?active_only=false")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check that we have exactly 2 products
        assert len(data) == 2, f"Expected 2 products, got {len(data)}. Products: {data}"
        
        # Check that both products are in the response
        names = [p["name"] for p in data]
        assert "Test Product" in names, f"Test Product not found in {names}"
        assert "Inactive Product" in names, f"Inactive Product not found in {names}"
    
    def test_create_product_creates_and_returns_product(self, client, sample_product_data):
        """
        GIVEN valid product data
        WHEN the POST /products endpoint is called
        THEN a new product should be created and returned
        """
        # Act
        response = client.post(
            "/api/v1/products/",
            json=sample_product_data,
            headers={"X-API-Key": "test-admin-key"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == sample_product_data["name"]
        assert data["description"] == sample_product_data["description"]
        assert float(data["base_price"]) == float(sample_product_data["base_price"])
        assert data["media"] == sample_product_data["media"]
        assert data["is_active"] == sample_product_data["is_active"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_create_product_fails_without_api_key(self, client, sample_product_data):
        """
        GIVEN valid product data but no API key
        WHEN the POST /products endpoint is called
        THEN a 401 Unauthorized response should be returned
        """
        # Arrange - Explicitly remove authentication for this test
        client.set_auth(None)
        
        try:
            # Act
            response = client.post(
                "/api/v1/products/",
                json=sample_product_data
            )
            
            # Assert
            assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
                f"Expected 401 Unauthorized, got {response.status_code}. Response: {response.text}"
        finally:
            # Restore authentication for other tests
            client.set_auth("test-admin-key")
    
    def test_get_product_by_id_returns_product_with_default_template(self, client, db_session, sample_product_data):
        """
        GIVEN a product with a default template
        WHEN the GET /products/{id} endpoint is called
        THEN the product with its default template should be returned
        """
        # This test would need the Template model implementation
        # Will be fully implemented with the Template model tests
        
        # Arrange
        product = Product(**sample_product_data)
        db_session.add(product)
        db_session.commit()
        
        # Act
        response = client.get(f"/api/v1/products/{product.id}")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == product.name
        assert data["description"] == product.description
        assert float(data["base_price"]) == float(product.base_price)
        assert data["media"] == product.media
        assert data["is_active"] == product.is_active
        assert data["default_template"] is None  # No template created yet
    
    def test_get_product_by_id_returns_404_for_nonexistent_product(self, client):
        """
        GIVEN a non-existent product ID
        WHEN the GET /products/{id} endpoint is called
        THEN a 404 Not Found response should be returned
        """
        # Act
        non_existent_id = uuid4()
        response = client.get(f"/api/v1/products/{non_existent_id}")
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_product_updates_and_returns_product(self, client, db_session, sample_product_data):
        """
        GIVEN an existing product and valid update data
        WHEN the PUT /products/{id} endpoint is called
        THEN the product should be updated and returned
        """
        # Arrange
        product = Product(**sample_product_data)
        db_session.add(product)
        db_session.commit()
        
        update_data = {
            "name": "Updated Product",
            "base_price": 29.99
        }
        
        # Act
        response = client.put(
            f"/api/v1/products/{product.id}",
            json=update_data,
            headers={"X-API-Key": "test-admin-key"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Product"
        assert float(data["base_price"]) == 29.99
        assert data["description"] == product.description  # Unchanged
        
        # Verify in database
        db_session.refresh(product)
        assert product.name == "Updated Product"
        assert float(product.base_price) == 29.99
    
    def test_delete_product_removes_product(self, client, db_session, sample_product_data):
        """
        GIVEN an existing product
        WHEN the DELETE /products/{id} endpoint is called
        THEN the product should be deleted
        """
        # Arrange
        product = Product(**sample_product_data)
        db_session.add(product)
        db_session.commit()
        product_id = product.id
        
        # Act
        response = client.delete(
            f"/api/v1/products/{product_id}",
            headers={"X-API-Key": "test-admin-key"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify in database
        deleted_product = db_session.query(Product).filter(Product.id == product_id).first()
        assert deleted_product is None
