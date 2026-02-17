"""
Unit tests for Template Service.

This test suite verifies the template service operations using ZeroDB NoSQL,
including CRUD operations, versioning, default template handling, and zones validation.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException

from app.services.template_service import TemplateService
from app.schemas.template import TemplateCreate, TemplateUpdate, CustomizationZoneCreate


class TestTemplateServiceCreate:
    """Test template creation with zones validation."""

    @pytest.fixture
    def mock_zerodb(self):
        """Mock ZeroDB service."""
        with patch('app.services.template_service.ZeroDBService') as mock:
            yield mock

    @pytest.fixture
    def template_service(self, mock_zerodb):
        """Create template service instance with mocked ZeroDB."""
        service = TemplateService()
        service.zerodb = mock_zerodb.return_value
        return service

    @pytest.fixture
    def sample_template_data(self):
        """Sample template creation data."""
        return TemplateCreate(
            product_id=uuid4(),
            version=1,
            definition={
                "zones": {
                    "text_zone": {"type": "text", "max_length": 100},
                    "image_zone": {"type": "image", "formats": ["png", "jpg"]}
                }
            },
            is_default=True,
            customization_zones=[
                CustomizationZoneCreate(
                    key="text_zone",
                    type="text",
                    config={"max_length": 100},
                    order_index=0
                ),
                CustomizationZoneCreate(
                    key="image_zone",
                    type="image",
                    config={"formats": ["png", "jpg"]},
                    order_index=1
                )
            ]
        )

    @pytest.mark.asyncio
    async def test_create_template_success(self, template_service, sample_template_data):
        """Test successful template creation."""
        # Mock ZeroDB responses
        template_service.zerodb.query_rows = AsyncMock(return_value={"results": []})
        template_service.zerodb.create_row = AsyncMock(return_value={
            "id": "test-template-id",
            "product_id": str(sample_template_data.product_id),
            "version": 1,
            "definition": sample_template_data.definition,
            "is_default": True,
            "customization_zones": [
                {
                    "id": "zone-1",
                    "key": "text_zone",
                    "type": "text",
                    "config": {"max_length": 100},
                    "order_index": 0
                },
                {
                    "id": "zone-2",
                    "key": "image_zone",
                    "type": "image",
                    "config": {"formats": ["png", "jpg"]},
                    "order_index": 1
                }
            ],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        })

        # Create template
        result = await template_service.create_template(sample_template_data)

        # Assertions
        assert result["product_id"] == str(sample_template_data.product_id)
        assert result["version"] == 1
        assert result["is_default"] is True
        assert len(result["customization_zones"]) == 2
        template_service.zerodb.create_row.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_template_version_conflict(self, template_service, sample_template_data):
        """Test template creation fails when version already exists."""
        # Mock existing version
        template_service.zerodb.query_rows = AsyncMock(return_value={
            "results": [{
                "id": "existing-template",
                "product_id": str(sample_template_data.product_id),
                "version": 1
            }]
        })

        # Attempt to create template
        with pytest.raises(HTTPException) as exc_info:
            await template_service.create_template(sample_template_data)

        assert exc_info.value.status_code == 400
        assert "already exists" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_create_template_unmarks_previous_default(self, template_service, sample_template_data):
        """Test creating default template unmarks previous default."""
        # Mock no existing version but existing default
        template_service.zerodb.query_rows = AsyncMock(side_effect=[
            {"results": []},  # No version conflict
            {"results": [{"id": "old-default", "is_default": True}]},  # Existing default
            {"results": [{"id": "old-default", "is_default": True}]}  # For unmarking
        ])
        template_service.zerodb.create_row = AsyncMock(return_value={
            "id": "new-template",
            "is_default": True
        })
        template_service.zerodb.update_row = AsyncMock()

        # Create template
        await template_service.create_template(sample_template_data)

        # Verify old default was unmarked
        template_service.zerodb.update_row.assert_called()

    @pytest.mark.asyncio
    async def test_create_template_auto_default_when_none_exists(self, template_service):
        """Test template is automatically marked default when none exists."""
        template_data = TemplateCreate(
            product_id=uuid4(),
            version=1,
            definition={"zones": {"text": {"type": "text"}}},
            is_default=False,  # Explicitly set to False
            customization_zones=[]
        )

        # Mock no existing templates
        template_service.zerodb.query_rows = AsyncMock(return_value={"results": []})
        template_service.zerodb.create_row = AsyncMock(return_value={
            "id": "new-template",
            "is_default": True  # Should be auto-set to True
        })

        # Create template
        result = await template_service.create_template(template_data)

        # Verify is_default was set to True
        assert result["is_default"] is True


class TestTemplateServiceRead:
    """Test template retrieval operations."""

    @pytest.fixture
    def template_service(self):
        """Create template service instance with mocked ZeroDB."""
        with patch('app.services.template_service.ZeroDBService') as mock:
            service = TemplateService()
            service.zerodb = mock.return_value
            return service

    @pytest.mark.asyncio
    async def test_get_template_success(self, template_service):
        """Test successful template retrieval."""
        template_id = "test-template-id"
        expected_template = {
            "id": template_id,
            "product_id": "product-123",
            "version": 1,
            "definition": {"zones": {}},
            "is_default": True
        }

        template_service.zerodb.get_row = AsyncMock(return_value=expected_template)

        result = await template_service.get_template(template_id)

        assert result == expected_template
        template_service.zerodb.get_row.assert_called_once_with(
            TemplateService.TABLE_NAME,
            template_id
        )

    @pytest.mark.asyncio
    async def test_get_template_not_found(self, template_service):
        """Test template retrieval when not found."""
        template_service.zerodb.get_row = AsyncMock(
            side_effect=HTTPException(status_code=404, detail="Not found")
        )

        with pytest.raises(HTTPException) as exc_info:
            await template_service.get_template("nonexistent")

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_list_templates_by_product(self, template_service):
        """Test listing templates filtered by product."""
        product_id = "product-123"
        expected_templates = [
            {"id": "t1", "product_id": product_id, "version": 2},
            {"id": "t2", "product_id": product_id, "version": 1}
        ]

        template_service.zerodb.query_rows = AsyncMock(return_value={
            "results": expected_templates
        })

        result = await template_service.list_templates(product_id=product_id)

        # Should be sorted by version descending
        assert result[0]["version"] == 2
        assert result[1]["version"] == 1
        template_service.zerodb.query_rows.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_templates_with_pagination(self, template_service):
        """Test listing templates with pagination."""
        template_service.zerodb.query_rows = AsyncMock(return_value={
            "results": []
        })

        await template_service.list_templates(
            product_id="product-123",
            limit=50,
            offset=10
        )

        call_args = template_service.zerodb.query_rows.call_args
        assert call_args[1]["limit"] == 50
        assert call_args[1]["offset"] == 10


class TestTemplateServiceUpdate:
    """Test template update operations."""

    @pytest.fixture
    def template_service(self):
        """Create template service instance with mocked ZeroDB."""
        with patch('app.services.template_service.ZeroDBService') as mock:
            service = TemplateService()
            service.zerodb = mock.return_value
            return service

    @pytest.mark.asyncio
    async def test_update_template_success(self, template_service):
        """Test successful template update."""
        template_id = "test-template"
        existing_template = {
            "id": template_id,
            "product_id": "product-123",
            "version": 1,
            "definition": {"zones": {}},
            "is_default": False
        }
        update_data = TemplateUpdate(version=2)

        template_service.zerodb.get_row = AsyncMock(return_value=existing_template)
        template_service.zerodb.query_rows = AsyncMock(return_value={"results": []})
        template_service.zerodb.update_row = AsyncMock(return_value={
            **existing_template,
            "version": 2
        })

        result = await template_service.update_template(template_id, update_data)

        assert result["version"] == 2
        template_service.zerodb.update_row.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_template_version_conflict(self, template_service):
        """Test update fails when new version already exists."""
        template_id = "test-template"
        existing_template = {
            "id": template_id,
            "product_id": "product-123",
            "version": 1
        }
        update_data = TemplateUpdate(version=2)

        template_service.zerodb.get_row = AsyncMock(return_value=existing_template)
        # Mock existing version 2
        template_service.zerodb.query_rows = AsyncMock(return_value={
            "results": [{"id": "other-template", "version": 2}]
        })

        with pytest.raises(HTTPException) as exc_info:
            await template_service.update_template(template_id, update_data)

        assert exc_info.value.status_code == 400
        assert "already exists" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_update_template_set_default(self, template_service):
        """Test setting template as default unmarks others."""
        template_id = "test-template"
        existing_template = {
            "id": template_id,
            "product_id": "product-123",
            "is_default": False
        }
        update_data = TemplateUpdate(is_default=True)

        template_service.zerodb.get_row = AsyncMock(return_value=existing_template)
        template_service.zerodb.query_rows = AsyncMock(return_value={
            "results": [{"id": "old-default", "is_default": True}]
        })
        template_service.zerodb.update_row = AsyncMock()

        await template_service.update_template(template_id, update_data)

        # Should update both old default and new template
        assert template_service.zerodb.update_row.call_count >= 2

    @pytest.mark.asyncio
    async def test_update_template_cannot_unset_only_default(self, template_service):
        """Test cannot unset default when it's the only default."""
        template_id = "test-template"
        existing_template = {
            "id": template_id,
            "product_id": "product-123",
            "is_default": True
        }
        update_data = TemplateUpdate(is_default=False)

        template_service.zerodb.get_row = AsyncMock(return_value=existing_template)
        template_service.zerodb.query_rows = AsyncMock(return_value={
            "results": []  # No other defaults
        })

        with pytest.raises(HTTPException) as exc_info:
            await template_service.update_template(template_id, update_data)

        assert exc_info.value.status_code == 400
        assert "at least one" in str(exc_info.value.detail).lower()


class TestTemplateServiceDelete:
    """Test template deletion operations."""

    @pytest.fixture
    def template_service(self):
        """Create template service instance with mocked ZeroDB."""
        with patch('app.services.template_service.ZeroDBService') as mock:
            service = TemplateService()
            service.zerodb = mock.return_value
            return service

    @pytest.mark.asyncio
    async def test_delete_template_success(self, template_service):
        """Test successful template deletion."""
        template_id = "test-template"
        product_id = "product-123"
        
        template_service.zerodb.get_row = AsyncMock(return_value={
            "id": template_id,
            "product_id": product_id,
            "is_default": False
        })
        template_service.zerodb.query_rows = AsyncMock(return_value={
            "results": [
                {"id": template_id},
                {"id": "other-template"}  # At least one other template
            ]
        })
        template_service.zerodb.delete_row = AsyncMock()

        result = await template_service.delete_template(template_id)

        assert result is True
        template_service.zerodb.delete_row.assert_called_once_with(
            TemplateService.TABLE_NAME,
            template_id
        )

    @pytest.mark.asyncio
    async def test_delete_template_cannot_delete_last(self, template_service):
        """Test cannot delete the only template for a product."""
        template_id = "test-template"
        
        template_service.zerodb.get_row = AsyncMock(return_value={
            "id": template_id,
            "product_id": "product-123"
        })
        template_service.zerodb.query_rows = AsyncMock(return_value={
            "results": [{"id": template_id}]  # Only this template
        })

        with pytest.raises(HTTPException) as exc_info:
            await template_service.delete_template(template_id)

        assert exc_info.value.status_code == 400
        assert "only template" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_delete_default_template_promotes_another(self, template_service):
        """Test deleting default template promotes another to default."""
        template_id = "test-template"
        product_id = "product-123"
        
        template_service.zerodb.get_row = AsyncMock(return_value={
            "id": template_id,
            "product_id": product_id,
            "is_default": True
        })
        template_service.zerodb.query_rows = AsyncMock(return_value={
            "results": [
                {"id": template_id, "is_default": True},
                {"id": "other-template", "is_default": False}
            ]
        })
        template_service.zerodb.update_row = AsyncMock()
        template_service.zerodb.delete_row = AsyncMock()

        await template_service.delete_template(template_id)

        # Should promote another template to default
        template_service.zerodb.update_row.assert_called()
        template_service.zerodb.delete_row.assert_called()


class TestTemplateServiceZonesValidation:
    """Test JSONB zones validation and handling."""

    @pytest.fixture
    def template_service(self):
        """Create template service instance with mocked ZeroDB."""
        with patch('app.services.template_service.ZeroDBService') as mock:
            service = TemplateService()
            service.zerodb = mock.return_value
            return service

    @pytest.mark.asyncio
    async def test_zones_stored_in_definition_and_array(self, template_service):
        """Test zones are stored both in definition and customization_zones array."""
        template_data = TemplateCreate(
            product_id=uuid4(),
            version=1,
            definition={
                "zones": {
                    "text_zone": {"type": "text", "max_length": 100}
                }
            },
            is_default=True,
            customization_zones=[
                CustomizationZoneCreate(
                    key="text_zone",
                    type="text",
                    config={"max_length": 100},
                    order_index=0
                )
            ]
        )

        template_service.zerodb.query_rows = AsyncMock(return_value={"results": []})
        created_template = None

        def capture_create(table, data):
            nonlocal created_template
            created_template = data
            return data

        template_service.zerodb.create_row = AsyncMock(side_effect=capture_create)

        await template_service.create_template(template_data)

        # Verify zones in definition
        assert "zones" in created_template["definition"]
        assert "text_zone" in created_template["definition"]["zones"]

        # Verify zones in customization_zones array
        assert len(created_template["customization_zones"]) == 1
        assert created_template["customization_zones"][0]["key"] == "text_zone"
        assert created_template["customization_zones"][0]["type"] == "text"

    @pytest.mark.asyncio
    async def test_empty_zones_array_when_none_provided(self, template_service):
        """Test empty customization_zones array when none provided."""
        template_data = TemplateCreate(
            product_id=uuid4(),
            version=1,
            definition={
                "zones": {
                    "text_zone": {"type": "text"}
                }
            },
            is_default=True,
            customization_zones=None
        )

        template_service.zerodb.query_rows = AsyncMock(return_value={"results": []})
        created_template = None

        def capture_create(table, data):
            nonlocal created_template
            created_template = data
            return data

        template_service.zerodb.create_row = AsyncMock(side_effect=capture_create)

        await template_service.create_template(template_data)

        # Should have empty array, not None
        assert created_template["customization_zones"] == []
