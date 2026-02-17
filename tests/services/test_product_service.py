"""
Integration tests for ProductService with ZeroDB.

These tests verify that the ProductService correctly interacts with ZeroDB
for all CRUD operations and maintains data integrity with denormalized storage.

Test Coverage:
    - Product creation with denormalized template data
    - Product retrieval by ID
    - Product listing with filtering and pagination
    - Product updates with template synchronization
    - Product deletion with cascade handling
    - Template synchronization
    - Option set management (add/remove)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import HTTPException

from app.schemas.product import ProductCreate, ProductUpdate
from app.services.product_service import ProductService


class TestProductService:
    """
    Test suite for ProductService with ZeroDB integration.

    Following BDD pattern with descriptive test method names.
    """

    @pytest.fixture
    def mock_zerodb_service(self):
        """Create a mock ZeroDB service for testing."""
        with patch("app.services.product_service.ZeroDBService") as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def product_service(self, mock_zerodb_service):
        """Create a ProductService instance with mocked ZeroDB."""
        with patch("app.services.product_service.settings") as mock_settings:
            mock_settings.ZERODB_PROJECT_ID = "test_project_id"
            mock_settings.AINATIVE_API_TOKEN = "test_token"
            mock_settings.AINATIVE_API_URL = "https://api.test.com/"
            service = ProductService()
            service.zerodb = mock_zerodb_service
            return service

    @pytest.fixture
    def sample_product_data(self):
        """Sample product creation data."""
        return ProductCreate(
            name="Test Product",
            description="A test product",
            base_price=24.99,
            media={"images": ["https://example.com/image.jpg"]},
            is_active=True
        )

    @pytest.fixture
    def sample_template_data(self):
        """Sample template data for denormalization."""
        return {
            "id": str(uuid4()),
            "version": 1,
            "definition": {
                "zones": [
                    {"type": "text", "key": "text1", "config": {}}
                ]
            },
            "is_default": True
        }

    @pytest.mark.asyncio
    async def test_create_product_without_template(
        self,
        product_service,
        mock_zerodb_service,
        sample_product_data
    ):
        """
        GIVEN valid product data without a template
        WHEN create_product is called
        THEN a product should be created in ZeroDB with correct data structure
        """
        # Arrange
        expected_product = {
            "id": "test-id-123",
            "name": "Test Product",
            "description": "A test product",
            "base_price": 24.99,
            "media": {"images": ["https://example.com/image.jpg"]},
            "is_active": True,
            "default_template": None,
            "templates_count": 0,
            "option_sets": []
        }
        mock_zerodb_service.create_row.return_value = expected_product

        # Act
        result = await product_service.create_product(sample_product_data)

        # Assert
        assert result == expected_product
        mock_zerodb_service.create_row.assert_called_once()
        call_args = mock_zerodb_service.create_row.call_args
        assert call_args[0][0] == "products"  # Table name
        created_data = call_args[0][1]
        assert created_data["name"] == "Test Product"
        assert created_data["base_price"] == 24.99
        assert created_data["is_active"] is True
        assert "id" in created_data
        assert "created_at" in created_data
        assert "updated_at" in created_data

    @pytest.mark.asyncio
    async def test_create_product_with_template(
        self,
        product_service,
        mock_zerodb_service,
        sample_product_data,
        sample_template_data
    ):
        """
        GIVEN valid product data with a default template
        WHEN create_product is called with template data
        THEN a product should be created with denormalized template data
        """
        # Arrange
        expected_product = {
            "id": "test-id-123",
            "name": "Test Product",
            "default_template": sample_template_data,
            "templates_count": 1
        }
        mock_zerodb_service.create_row.return_value = expected_product

        # Act
        result = await product_service.create_product(
            sample_product_data,
            default_template=sample_template_data
        )

        # Assert
        assert result["default_template"] == sample_template_data
        assert result["templates_count"] == 1
        call_args = mock_zerodb_service.create_row.call_args[0][1]
        assert call_args["default_template"] == sample_template_data

    @pytest.mark.asyncio
    async def test_get_product_returns_product_with_template(
        self,
        product_service,
        mock_zerodb_service,
        sample_template_data
    ):
        """
        GIVEN a product ID
        WHEN get_product is called
        THEN the product with denormalized template data should be returned
        """
        # Arrange
        product_id = str(uuid4())
        expected_product = {
            "id": product_id,
            "name": "Test Product",
            "base_price": 24.99,
            "default_template": sample_template_data
        }
        mock_zerodb_service.get_row.return_value = expected_product

        # Act
        result = await product_service.get_product(product_id)

        # Assert
        assert result == expected_product
        mock_zerodb_service.get_row.assert_called_once_with("products", product_id)

    @pytest.mark.asyncio
    async def test_get_product_raises_404_when_not_found(
        self,
        product_service,
        mock_zerodb_service
    ):
        """
        GIVEN a non-existent product ID
        WHEN get_product is called
        THEN an HTTPException with 404 status should be raised
        """
        # Arrange
        product_id = str(uuid4())
        mock_zerodb_service.get_row.side_effect = HTTPException(
            status_code=404,
            detail="Not found"
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await product_service.get_product(product_id)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_list_products_with_active_filter(
        self,
        product_service,
        mock_zerodb_service
    ):
        """
        GIVEN products in ZeroDB
        WHEN list_products is called with active_only=True
        THEN only active products should be queried
        """
        # Arrange
        expected_products = [
            {"id": "1", "name": "Product 1", "is_active": True},
            {"id": "2", "name": "Product 2", "is_active": True}
        ]
        mock_zerodb_service.query_rows.return_value = {
            "results": expected_products
        }

        # Act
        result = await product_service.list_products(
            skip=0,
            limit=10,
            active_only=True
        )

        # Assert
        assert result == expected_products
        mock_zerodb_service.query_rows.assert_called_once()
        call_args = mock_zerodb_service.query_rows.call_args
        assert call_args[1]["filter_query"]["is_active"] is True

    @pytest.mark.asyncio
    async def test_list_products_with_name_filter(
        self,
        product_service,
        mock_zerodb_service
    ):
        """
        GIVEN products in ZeroDB
        WHEN list_products is called with name_filter
        THEN products should be queried with regex filter
        """
        # Arrange
        expected_products = [
            {"id": "1", "name": "T-Shirt", "is_active": True}
        ]
        mock_zerodb_service.query_rows.return_value = {
            "results": expected_products
        }

        # Act
        result = await product_service.list_products(
            name_filter="shirt"
        )

        # Assert
        assert result == expected_products
        call_args = mock_zerodb_service.query_rows.call_args
        filter_query = call_args[1]["filter_query"]
        assert "name" in filter_query
        assert filter_query["name"]["$regex"] == "shirt"
        assert filter_query["name"]["$options"] == "i"

    @pytest.mark.asyncio
    async def test_list_products_with_pagination(
        self,
        product_service,
        mock_zerodb_service
    ):
        """
        GIVEN products in ZeroDB
        WHEN list_products is called with skip and limit
        THEN products should be queried with correct pagination
        """
        # Arrange
        expected_products = [
            {"id": "11", "name": "Product 11"},
            {"id": "12", "name": "Product 12"}
        ]
        mock_zerodb_service.query_rows.return_value = expected_products

        # Act
        result = await product_service.list_products(
            skip=10,
            limit=2,
            active_only=False
        )

        # Assert
        assert result == expected_products
        call_args = mock_zerodb_service.query_rows.call_args
        assert call_args[1]["limit"] == 2
        assert call_args[1]["offset"] == 10

    @pytest.mark.asyncio
    async def test_update_product_with_partial_data(
        self,
        product_service,
        mock_zerodb_service
    ):
        """
        GIVEN an existing product
        WHEN update_product is called with partial data
        THEN the product should be updated with merged data
        """
        # Arrange
        product_id = str(uuid4())
        existing_product = {
            "id": product_id,
            "name": "Old Name",
            "description": "Old Description",
            "base_price": 19.99,
            "is_active": True,
            "default_template": None
        }
        mock_zerodb_service.get_row.return_value = existing_product

        update_data = ProductUpdate(name="New Name", base_price=29.99)
        updated_product = {**existing_product, "name": "New Name", "base_price": 29.99}
        mock_zerodb_service.update_row.return_value = updated_product

        # Act
        result = await product_service.update_product(product_id, update_data)

        # Assert
        assert result["name"] == "New Name"
        assert result["base_price"] == 29.99
        assert result["description"] == "Old Description"  # Unchanged
        mock_zerodb_service.update_row.assert_called_once()
        call_args = mock_zerodb_service.update_row.call_args[0]
        assert call_args[1] == product_id
        assert "updated_at" in call_args[2]

    @pytest.mark.asyncio
    async def test_delete_product_with_cascade(
        self,
        product_service,
        mock_zerodb_service
    ):
        """
        GIVEN an existing product
        WHEN delete_product is called with cascade=True
        THEN the product should be deleted from ZeroDB
        """
        # Arrange
        product_id = str(uuid4())
        existing_product = {"id": product_id, "name": "Test Product"}
        mock_zerodb_service.get_row.return_value = existing_product
        mock_zerodb_service.delete_row.return_value = {"success": True}

        # Act
        result = await product_service.delete_product(product_id, cascade=True)

        # Assert
        assert result is True
        mock_zerodb_service.get_row.assert_called_once_with("products", product_id)
        mock_zerodb_service.delete_row.assert_called_once_with("products", product_id)

    @pytest.mark.asyncio
    async def test_delete_product_raises_404_when_not_found(
        self,
        product_service,
        mock_zerodb_service
    ):
        """
        GIVEN a non-existent product ID
        WHEN delete_product is called
        THEN an HTTPException with 404 status should be raised
        """
        # Arrange
        product_id = str(uuid4())
        mock_zerodb_service.get_row.side_effect = HTTPException(
            status_code=404,
            detail="Not found"
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await product_service.delete_product(product_id)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_product_with_default_template_returns_template_field(
        self,
        product_service,
        mock_zerodb_service,
        sample_template_data
    ):
        """
        GIVEN a product with default template
        WHEN get_product_with_default_template is called
        THEN the product with default_template field should be returned
        """
        # Arrange
        product_id = str(uuid4())
        product_with_template = {
            "id": product_id,
            "name": "Test Product",
            "default_template": sample_template_data
        }
        mock_zerodb_service.get_row.return_value = product_with_template

        # Act
        result = await product_service.get_product_with_default_template(product_id)

        # Assert
        assert result["default_template"] == sample_template_data

    @pytest.mark.asyncio
    async def test_get_product_with_default_template_ensures_field_exists(
        self,
        product_service,
        mock_zerodb_service
    ):
        """
        GIVEN a product without default_template field
        WHEN get_product_with_default_template is called
        THEN the product with default_template=None should be returned
        """
        # Arrange
        product_id = str(uuid4())
        product_without_template = {
            "id": product_id,
            "name": "Test Product"
        }
        mock_zerodb_service.get_row.return_value = product_without_template

        # Act
        result = await product_service.get_product_with_default_template(product_id)

        # Assert
        assert "default_template" in result
        assert result["default_template"] is None

    @pytest.mark.asyncio
    async def test_sync_template_data_updates_denormalized_template(
        self,
        product_service,
        mock_zerodb_service,
        sample_template_data
    ):
        """
        GIVEN a product with an existing template
        WHEN sync_template_data is called with new template data
        THEN the denormalized template should be updated
        """
        # Arrange
        product_id = str(uuid4())
        existing_product = {
            "id": product_id,
            "name": "Test Product",
            "default_template": {"version": 1}
        }
        mock_zerodb_service.get_row.return_value = existing_product

        new_template = {**sample_template_data, "version": 2}
        updated_product = {
            **existing_product,
            "default_template": new_template
        }
        mock_zerodb_service.update_row.return_value = updated_product

        # Act
        result = await product_service.sync_template_data(product_id, new_template)

        # Assert
        assert result["default_template"]["version"] == 2
        mock_zerodb_service.update_row.assert_called_once()
        call_args = mock_zerodb_service.update_row.call_args[0][2]
        assert call_args["default_template"] == new_template

    @pytest.mark.asyncio
    async def test_add_option_set_appends_to_array(
        self,
        product_service,
        mock_zerodb_service
    ):
        """
        GIVEN a product with existing option sets
        WHEN add_option_set is called
        THEN the new option set should be appended to the option_sets array
        """
        # Arrange
        product_id = str(uuid4())
        existing_product = {
            "id": product_id,
            "name": "Test Product",
            "option_sets": [
                {"id": "opt1", "name": "Size"}
            ]
        }
        mock_zerodb_service.get_row.return_value = existing_product

        new_option_set = {
            "id": "opt2",
            "name": "Color",
            "options": [{"value": "Red"}, {"value": "Blue"}]
        }

        updated_product = {
            **existing_product,
            "option_sets": [
                {"id": "opt1", "name": "Size"},
                {"id": "opt2", "name": "Color", "options": [{"value": "Red"}, {"value": "Blue"}]}
            ]
        }
        mock_zerodb_service.update_row.return_value = updated_product

        # Act
        result = await product_service.add_option_set(product_id, new_option_set)

        # Assert
        assert len(result["option_sets"]) == 2
        assert result["option_sets"][1]["id"] == "opt2"

    @pytest.mark.asyncio
    async def test_add_option_set_initializes_empty_array(
        self,
        product_service,
        mock_zerodb_service
    ):
        """
        GIVEN a product without option_sets field
        WHEN add_option_set is called
        THEN option_sets array should be initialized and option added
        """
        # Arrange
        product_id = str(uuid4())
        existing_product = {
            "id": product_id,
            "name": "Test Product"
        }
        mock_zerodb_service.get_row.return_value = existing_product

        new_option_set = {"id": "opt1", "name": "Size"}
        updated_product = {
            **existing_product,
            "option_sets": [{"id": "opt1", "name": "Size"}]
        }
        mock_zerodb_service.update_row.return_value = updated_product

        # Act
        result = await product_service.add_option_set(product_id, new_option_set)

        # Assert
        assert len(result["option_sets"]) == 1
        assert result["option_sets"][0]["id"] == "opt1"

    @pytest.mark.asyncio
    async def test_remove_option_set_filters_out_by_id(
        self,
        product_service,
        mock_zerodb_service
    ):
        """
        GIVEN a product with multiple option sets
        WHEN remove_option_set is called
        THEN the specified option set should be removed from the array
        """
        # Arrange
        product_id = str(uuid4())
        existing_product = {
            "id": product_id,
            "name": "Test Product",
            "option_sets": [
                {"id": "opt1", "name": "Size"},
                {"id": "opt2", "name": "Color"}
            ]
        }
        mock_zerodb_service.get_row.return_value = existing_product

        updated_product = {
            **existing_product,
            "option_sets": [{"id": "opt2", "name": "Color"}]
        }
        mock_zerodb_service.update_row.return_value = updated_product

        # Act
        result = await product_service.remove_option_set(product_id, "opt1")

        # Assert
        assert len(result["option_sets"]) == 1
        assert result["option_sets"][0]["id"] == "opt2"

    @pytest.mark.asyncio
    async def test_create_product_converts_decimal_to_float(
        self,
        product_service,
        mock_zerodb_service,
        sample_product_data
    ):
        """
        GIVEN product data with Decimal base_price
        WHEN create_product is called
        THEN the price should be converted to float for JSON serialization
        """
        # Arrange
        from decimal import Decimal
        sample_product_data.base_price = Decimal("24.99")

        mock_zerodb_service.create_row.return_value = {"id": "test-id"}

        # Act
        await product_service.create_product(sample_product_data)

        # Assert
        call_args = mock_zerodb_service.create_row.call_args[0][1]
        assert isinstance(call_args["base_price"], float)
        assert call_args["base_price"] == 24.99

    @pytest.mark.asyncio
    async def test_update_product_converts_decimal_to_float(
        self,
        product_service,
        mock_zerodb_service
    ):
        """
        GIVEN update data with Decimal base_price
        WHEN update_product is called
        THEN the price should be converted to float for JSON serialization
        """
        # Arrange
        from decimal import Decimal

        product_id = str(uuid4())
        existing_product = {
            "id": product_id,
            "name": "Test Product",
            "base_price": 19.99
        }
        mock_zerodb_service.get_row.return_value = existing_product

        update_data = ProductUpdate(base_price=Decimal("29.99"))
        mock_zerodb_service.update_row.return_value = {
            **existing_product,
            "base_price": 29.99
        }

        # Act
        await product_service.update_product(product_id, update_data)

        # Assert
        call_args = mock_zerodb_service.update_row.call_args[0][2]
        assert isinstance(call_args["base_price"], float)
        assert call_args["base_price"] == 29.99
