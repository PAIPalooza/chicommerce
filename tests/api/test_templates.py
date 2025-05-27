"""
Integration tests for Template API endpoints.
"""
import pytest
import json
from uuid import uuid4, UUID
from fastapi import status

from app.models.product import Product
from app.models.template import Template, CustomizationZone


@pytest.fixture
def sample_product_id(db_session, sample_product_data):
    """Fixture to create a product and return its ID."""
    product = Product(**sample_product_data)
    db_session.add(product)
    db_session.commit()
    return product.id


class TestTemplatesAPI:
    """
    Test suite for Template API endpoints.
    
    Following BDD pattern with descriptive test method names.
    """
    
    def test_get_templates_by_product_returns_templates(self, client, db_session, sample_product_id):
        """
        GIVEN a product with templates
        WHEN the GET /templates endpoint is called with product_id
        THEN the templates for that product should be returned
        """
        # Arrange
        template1 = Template(
            product_id=sample_product_id,
            version=1,
            definition={"zones": {"text_front": {"type": "text"}}},
            is_default=True
        )
        template2 = Template(
            product_id=sample_product_id,
            version=2,
            definition={"zones": {"text_front": {"type": "text"}, "image_back": {"type": "image"}}},
            is_default=False
        )
        db_session.add(template1)
        db_session.add(template2)
        db_session.commit()
        
        # Act
        response = client.get(f"/api/v1/templates/?product_id={sample_product_id}")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        versions = [t["version"] for t in data]
        assert 1 in versions
        assert 2 in versions
    
    def test_get_templates_without_product_id_returns_400(self, client):
        """
        GIVEN no product_id parameter
        WHEN the GET /templates endpoint is called
        THEN a 400 Bad Request response should be returned
        """
        # Act
        response = client.get("/api/v1/templates/")
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_template_creates_and_returns_template(self, client, sample_product_id, sample_template_data):
        """
        GIVEN valid template data
        WHEN the POST /templates endpoint is called
        THEN a new template should be created and returned
        """
        # Arrange
        template_data = sample_template_data
        template_data["product_id"] = sample_product_id
        
        # Act
        response = client.post(
            "/api/v1/templates/",
            json=template_data,
            headers={"X-API-Key": "test-admin-key"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["product_id"] == str(sample_product_id)
        assert data["version"] == template_data["version"]
        assert data["definition"] == template_data["definition"]
        assert data["is_default"] == template_data["is_default"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
        
        # Check customization zones if they were created
        if "customization_zones" in template_data:
            assert len(data["customization_zones"]) == len(template_data["customization_zones"])
            for zone in data["customization_zones"]:
                assert zone["template_id"] == data["id"]
    
    def test_create_template_fails_without_api_key(self, client, sample_product_id, sample_template_data):
        """
        GIVEN valid template data but no API key
        WHEN the POST /templates endpoint is called
        THEN a 403 Forbidden response should be returned
        """
        # Arrange
        template_data = sample_template_data
        template_data["product_id"] = sample_product_id
        
        # Act
        response = client.post(
            "/api/v1/templates/",
            json=template_data
        )
        
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_create_template_fails_with_nonexistent_product(self, client, sample_template_data):
        """
        GIVEN template data with a non-existent product_id
        WHEN the POST /templates endpoint is called
        THEN a 404 Not Found response should be returned
        """
        # Arrange
        template_data = sample_template_data
        template_data["product_id"] = uuid4()
        
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
        GIVEN an existing template
        WHEN the DELETE /templates/{id} endpoint is called
        THEN the template should be deleted
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
        template_id = template.id
        
        # Act
        response = client.delete(
            f"/api/v1/templates/{template_id}",
            headers={"X-API-Key": "test-admin-key"}
        )
        
        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify in database
        deleted_template = db_session.query(Template).filter(Template.id == template_id).first()
        assert deleted_template is None
        
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
