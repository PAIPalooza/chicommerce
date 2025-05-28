"""
Integration tests for Template API endpoints.

Following BDD (Behavior-Driven Development) patterns and TDD principles.
"""
import pytest
import json
from uuid import uuid4, UUID
from fastapi import status

from app.models.product import Product
from app.models.template import Template, CustomizationZone
from app.schemas.template import TemplateCreate, TemplateUpdate


class TestTemplatesAPI:
    """
    Test suite for Template API endpoints.
    
    Following BDD pattern with descriptive test method names.
    """
    
    # --- List Templates ---
    
    def test_list_templates_returns_templates_for_product(self, client, sample_template):
        """
        GIVEN a product with templates
        WHEN the GET /templates endpoint is called with product_id
        THEN the templates for that product should be returned
        """
        # Act
        response = client.get(f"/api/v1/templates/?product_id={sample_template.product_id}")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(sample_template.id)
        assert data[0]["version"] == 1
        assert data[0]["is_default"] is True
    
    def test_list_templates_requires_product_id(self, client):
        """
        GIVEN no product_id parameter
        WHEN the GET /templates endpoint is called
        THEN a 400 Bad Request response should be returned
        """
        # Act
        response = client.get("/api/v1/templates/")
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Product ID is required for listing templates"
    
    # --- Create Template ---
    
    def test_create_template_creates_and_returns_template(self, client, sample_product):
        """
        GIVEN valid template data
        WHEN the POST /templates endpoint is called
        THEN a new template should be created and returned
        """
        # Arrange
        template_data = {
            "product_id": str(sample_product.id),
            "version": 1,
            "definition": {
                "zones": {
                    "text_1": {"type": "text", "max_length": 100},
                    "image_1": {"type": "image", "formats": ["png", "jpg"]}
                }
            },
            "is_default": True,
            "customization_zones": [
                {
                    "key": "text_1",
                    "type": "text",
                    "config": {"max_length": 100},
                    "order_index": 0
                },
                {
                    "key": "image_1",
                    "type": "image",
                    "config": {"formats": ["png", "jpg"]},
                    "order_index": 1
                }
            ]
        }
        
        # Act
        response = client.post(
            "/api/v1/templates/",
            json=template_data,
            headers={"X-API-Key": "test-admin-key"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED, response.text
        data = response.json()
        assert data["product_id"] == str(sample_product.id)
        assert data["version"] == 1
        assert data["is_default"] is True
        assert len(data["customization_zones"]) == 2
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_create_template_validates_duplicate_version(self, client, sample_template):
        """
        GIVEN a template with a version that already exists for the product
        WHEN the POST /templates endpoint is called
        THEN a 400 Bad Request response should be returned
        """
        # Arrange
        template_data = {
            "product_id": str(sample_template.product_id),
            "version": 1,  # Duplicate version
            "definition": {"zones": {"test": {"type": "text"}}},
            "is_default": False
        }
        
        # Act
        response = client.post(
            "/api/v1/templates/",
            json=template_data,
            headers={"X-API-Key": "test-admin-key"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists for this product" in response.json()["detail"]
    
    # --- Get Template ---
    
    def test_get_template_returns_template(self, client, sample_template):
        """
        GIVEN an existing template ID
        WHEN the GET /templates/{template_id} endpoint is called
        THEN the template should be returned
        """
        # Act
        response = client.get(f"/api/v1/templates/{sample_template.id}")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(sample_template.id)
        assert data["version"] == sample_template.version
        assert "customization_zones" in data
    
    def test_get_nonexistent_template_returns_404(self, client):
        """
        GIVEN a non-existent template ID
        WHEN the GET /templates/{template_id} endpoint is called
        THEN a 404 Not Found response should be returned
        """
        # Arrange
        non_existent_id = "00000000-0000-0000-0000-000000000000"
        
        # Act
        response = client.get(f"/api/v1/templates/{non_existent_id}")
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    # --- Update Template ---
    
    def test_update_template_updates_and_returns_template(self, client, sample_template):
        """
        GIVEN an existing template and update data
        WHEN the PUT /templates/{template_id} endpoint is called
        THEN the template should be updated and returned
        """
        # Arrange
        update_data = {
            "version": 2,
            "is_default": False,
            "definition": {"zones": {"updated_zone": {"type": "text"}}},
            "customization_zones": [
                {"key": "updated_zone", "type": "text", "order_index": 0}
            ]
        }
        
        # Act
        response = client.put(
            f"/api/v1/templates/{sample_template.id}",
            json=update_data,
            headers={"X-API-Key": "test-admin-key"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["version"] == 2
        assert data["is_default"] is False
        assert "updated_zone" in data["definition"]["zones"]
        assert len(data["customization_zones"]) == 1
        assert data["customization_zones"][0]["key"] == "updated_zone"
    
    # --- Delete Template ---
    
    def test_delete_template_deletes_template(self, client, db_session, sample_template):
        """
        GIVEN an existing template ID
        WHEN the DELETE /templates/{template_id} endpoint is called
        THEN the template should be deleted
        """
        # Arrange - create another template for the same product
        another_template = Template(
            product_id=sample_template.product_id,
            version=2,
            definition={"zones": {"another_zone": {"type": "text"}}},
            is_default=False
        )
        db_session.add(another_template)
        db_session.commit()
        
        # Act
        response = client.delete(
            f"/api/v1/templates/{sample_template.id}",
            headers={"X-API-Key": "test-admin-key"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify template is deleted
        response = client.get(f"/api/v1/templates/{sample_template.id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_last_template_returns_error(self, client, sample_template):
        """
        GIVEN the last template for a product
        WHEN the DELETE /templates/{template_id} endpoint is called
        THEN a 400 Bad Request response should be returned
        """
        # Act
        response = client.delete(
            f"/api/v1/templates/{sample_template.id}",
            headers={"X-API-Key": "test-admin-key"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cannot delete the only template for a product" == response.json()["detail"]
    
    # --- Authorization ---
    
    def test_create_template_requires_authentication(self, client, sample_product):
        """
        GIVEN no API key
        WHEN the POST /templates endpoint is called
        THEN a 401 Unauthorized response should be returned
        """
        # Remove authentication for this test
        client.set_auth(None)
        
        # Act
        response = client.post(
            "/api/v1/templates/",
            json={"product_id": str(sample_product.id), "version": 1, "definition": {"zones": {}}},
        )
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Restore authentication for other tests
        client.set_auth("test-admin-key")
    
    def test_update_template_requires_authentication(self, client, sample_template):
        """
        GIVEN no API key
        WHEN the PUT /templates/{template_id} endpoint is called
        THEN a 401 Unauthorized response should be returned
        """
        # Remove authentication for this test
        client.set_auth(None)
        
        # Act
        response = client.put(
            f"/api/v1/templates/{sample_template.id}",
            json={"version": 2}
        )
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Restore authentication for other tests
        client.set_auth("test-admin-key")
    
    def test_delete_template_requires_authentication(self, client, sample_template):
        """
        GIVEN no API key
        WHEN the DELETE /templates/{template_id} endpoint is called
        THEN a 401 Unauthorized response should be returned
        """
        # Remove authentication for this test
        client.set_auth(None)
        
        # Act
        response = client.delete(f"/api/v1/templates/{sample_template.id}")
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Restore authentication for other tests
        client.set_auth("test-admin-key")
    
    def test_create_template_fails_with_invalid_api_key(self, client, sample_product_id, sample_template_data, monkeypatch):
        """
        GIVEN valid template data but an invalid API key
        WHEN the POST /templates endpoint is called
        THEN a 403 Forbidden response should be returned
        """
        # Arrange
        template_data = sample_template_data.copy()
        template_data["product_id"] = str(sample_product_id)  # Convert UUID to string for JSON serialization
        
        # Mock the settings.ADMIN_API_KEY to ensure our test key is different
        monkeypatch.setattr("app.core.config.settings.ADMIN_API_KEY", "valid-admin-key")
        
        # Remove any existing authentication
        client.set_auth(None)
        
        # Act - First test with no API key at all
        response = client.post(
            "/api/v1/templates/",
            json=template_data
        )
        
        # Assert - Should be 401 Unauthorized for missing API key
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Act - Now test with an invalid API key
        response = client.post(
            "/api/v1/templates/",
            json=template_data,
            headers={"X-API-Key": "invalid-api-key"}
        )
        
        # Assert - Should be 403 Forbidden for invalid API key
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Invalid API Key" in response.json()["detail"]
        
        # Restore valid API key for other tests
        client.set_auth("test-admin-key")
    
    def test_create_template_fails_with_nonexistent_product(self, client, sample_template_data):
        """
        GIVEN template data with a non-existent product_id
        WHEN the POST /templates endpoint is called
        THEN a 404 Not Found response should be returned
        """
        # Arrange
        template_data = sample_template_data.copy()  # Create a copy to avoid modifying the fixture
        template_data["product_id"] = str(uuid4())  # Convert UUID to string for JSON serialization
        
        # Act
        response = client.post(
            "/api/v1/templates/",
            json=template_data,
            headers={"X-API-Key": "test-admin-key"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_get_template_by_id_returns_template(self, client, db_session, sample_product_id):
        """
        GIVEN an existing template
        WHEN the GET /templates/{id} endpoint is called
        THEN the template should be returned
        """
        # Arrange
        template = Template(
            product_id=sample_product_id,
            version=1,
            definition={"zones": {"text_front": {"type": "text"}}},
            is_default=True
        )
        db_session.add(template)
        db_session.commit()
        
        zone = CustomizationZone(
            template_id=template.id,
            key="text_front",
            type="text",
            config={"max_length": 50},
            order_index=0
        )
        db_session.add(zone)
        db_session.commit()
        
        # Act
        response = client.get(f"/api/v1/templates/{template.id}")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(template.id)
        assert data["product_id"] == str(sample_product_id)
        assert data["version"] == 1
        assert data["definition"] == {"zones": {"text_front": {"type": "text"}}}
        assert data["is_default"] is True
        assert len(data["customization_zones"]) == 1
        assert data["customization_zones"][0]["key"] == "text_front"
    
    def test_get_template_by_id_returns_404_for_nonexistent_template(self, client):
        """
        GIVEN a non-existent template ID
        WHEN the GET /templates/{id} endpoint is called
        THEN a 404 Not Found response should be returned
        """
        # Act
        non_existent_id = uuid4()
        response = client.get(f"/api/v1/templates/{non_existent_id}")
        
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_template_updates_and_returns_template(self, client, db_session, sample_product_id):
        """
        GIVEN an existing template and valid update data
        WHEN the PUT /templates/{id} endpoint is called
        THEN the template should be updated and returned
        """
        # Arrange
        template = Template(
            product_id=sample_product_id,
            version=1,
            definition={"zones": {"text_front": {"type": "text"}}},
            is_default=False
        )
        db_session.add(template)
        db_session.commit()
        
        update_data = {
            "definition": {"zones": {"text_front": {"type": "text"}, "image_back": {"type": "image"}}},
            "is_default": True
        }
        
        # Act
        response = client.put(
            f"/api/v1/templates/{template.id}",
            json=update_data,
            headers={"X-API-Key": "test-admin-key"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["definition"] == update_data["definition"]
        assert data["is_default"] == update_data["is_default"]
        
        # Verify in database
        db_session.refresh(template)
        assert template.definition == update_data["definition"]
        assert template.is_default == update_data["is_default"]
    
    def test_delete_template_removes_template(self, client, db_session, sample_product_id):
        """
        GIVEN multiple existing templates for a product
        WHEN the DELETE /templates/{id} endpoint is called
        THEN the specified template should be deleted and another template should be made default if needed
        """
        # Arrange - create two templates for the product
        template1 = Template(
            product_id=sample_product_id,
            version=1,
            definition={"zones": {"text_front": {"type": "text"}}},
            is_default=True
        )
        template2 = Template(
            product_id=sample_product_id,
            version=2,
            definition={"zones": {"text_back": {"type": "text"}}},
            is_default=False
        )
        db_session.add_all([template1, template2])
        db_session.commit()
        
        # Act - delete the first template
        response = client.delete(
            f"/api/v1/templates/{template1.id}",
            headers={"X-API-Key": "test-admin-key"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify template1 is deleted
        deleted_template = db_session.get(Template, template1.id)
        assert deleted_template is None
        
        # Verify template2 is now the default
        db_session.refresh(template2)
        assert template2.is_default is True
        
    def test_product_with_default_template_includes_template_data(self, client, db_session, sample_product_id):
        """
        GIVEN a product with a default template
        WHEN the GET /products/{id} endpoint is called
        THEN the product should include the default template data
        """
        # Arrange
        template = Template(
            product_id=sample_product_id,
            version=1,
            definition={"zones": {"text_front": {"type": "text"}}},
            is_default=True
        )
        db_session.add(template)
        db_session.commit()
        
        # Act
        response = client.get(f"/api/v1/products/{sample_product_id}")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["default_template"] is not None
        assert data["default_template"]["id"] == str(template.id)
        assert data["default_template"]["version"] == 1
        assert data["default_template"]["definition"] == {"zones": {"text_front": {"type": "text"}}}
