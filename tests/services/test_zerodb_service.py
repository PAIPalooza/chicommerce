"""
Tests for ZeroDB service using TDD approach.

This module tests the ZeroDB service functionality including:
- Service initialization and configuration
- CRUD operations (create, read, query, update, delete)
- Error handling and custom exceptions
- Retry logic with exponential backoff
- HTTP request handling
- MongoDB-style filter support
"""
import pytest
import httpx
from unittest.mock import Mock, AsyncMock, patch
from typing import Any, Dict

from app.services.zerodb_service import (
    ZeroDBService,
    ZeroDBError,
    ZeroDBConnectionError,
    ZeroDBNotFoundError,
    ZeroDBValidationError,
    get_zerodb_service,
)
from app.core.config import settings
from fastapi import HTTPException


class TestZeroDBServiceInitialization:
    """Test suite for ZeroDBService initialization."""

    def test_initialize_with_settings_project_id(self, monkeypatch):
        """Should initialize service with project ID from settings."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")
        monkeypatch.setattr(settings, "ZERODB_TIMEOUT", 30)
        monkeypatch.setattr(settings, "ZERODB_MAX_RETRIES", 3)

        service = ZeroDBService()
        assert service.project_id == "proj_test_123"
        assert service.timeout == 30
        assert service.max_retries == 3

    def test_initialize_with_correct_base_url(self, monkeypatch):
        """Should construct correct base URL from settings."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")
        monkeypatch.setattr(settings, "AINATIVE_API_URL", "https://api.ainative.studio/")

        service = ZeroDBService()
        expected_url = "https://api.ainative.studio/v1/public/zerodb/proj_test_123/database"
        assert service.base_url == expected_url

    def test_initialize_with_correct_headers(self, monkeypatch):
        """Should set Authorization and Content-Type headers."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token_456")

        service = ZeroDBService()
        assert service.headers["Authorization"] == "Bearer test_token_456"
        assert service.headers["Content-Type"] == "application/json"

    def test_initialize_with_custom_project_id(self, monkeypatch):
        """Should use custom project ID when provided."""
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = ZeroDBService(project_id="proj_custom_789")
        assert service.project_id == "proj_custom_789"

    def test_initialize_with_custom_timeout(self, monkeypatch):
        """Should use custom timeout when provided."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = ZeroDBService(timeout=60)
        assert service.timeout == 60

    def test_initialize_with_custom_max_retries(self, monkeypatch):
        """Should use custom max_retries when provided."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = ZeroDBService(max_retries=5)
        assert service.max_retries == 5

    def test_raises_error_when_project_id_missing(self, monkeypatch):
        """Should raise ZeroDBValidationError when project ID is not set."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        with pytest.raises(ZeroDBValidationError) as exc_info:
            ZeroDBService()
        assert "ZERODB_PROJECT_ID is required" in str(exc_info.value)

    def test_raises_error_when_api_token_missing(self, monkeypatch):
        """Should raise ZeroDBValidationError when API token is not set."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "")

        with pytest.raises(ZeroDBValidationError) as exc_info:
            ZeroDBService()
        assert "AINATIVE_API_TOKEN is required" in str(exc_info.value)


class TestZeroDBServiceCreateRow:
    """Test suite for create_row method."""

    @pytest.mark.asyncio
    async def test_create_row_with_valid_data(self, monkeypatch):
        """Should create row and return created data."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = ZeroDBService()

        mock_response = {
            "id": "row_123",
            "name": "Test Product",
            "price": 24.99,
            "created_at": "2026-01-01T00:00:00Z"
        }

        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await service.create_row("products", {
                "name": "Test Product",
                "price": 24.99
            })

            assert result == mock_response
            mock_request.assert_called_once()
            args = mock_request.call_args
            assert args[0][0] == "POST"
            assert "/tables/products/rows" in args[0][1]

    @pytest.mark.asyncio
    async def test_create_row_sends_correct_payload(self, monkeypatch):
        """Should send correct JSON payload in request."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = ZeroDBService()
        test_data = {"name": "Product", "price": 19.99, "active": True}

        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"id": "row_123"}

            await service.create_row("products", test_data)

            args = mock_request.call_args
            assert args[1]["json_data"] == test_data

    @pytest.mark.asyncio
    async def test_create_row_raises_error_for_empty_table_name(self, monkeypatch):
        """Should raise ZeroDBValidationError for empty table name."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = ZeroDBService()

        with pytest.raises(ZeroDBValidationError) as exc_info:
            await service.create_row("", {"name": "Product"})
        assert "Table name is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_row_raises_error_for_empty_data(self, monkeypatch):
        """Should raise ZeroDBValidationError for empty data."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = ZeroDBService()

        with pytest.raises(ZeroDBValidationError) as exc_info:
            await service.create_row("products", {})
        assert "Data is required for row creation" in str(exc_info.value)


class TestZeroDBServiceGetRow:
    """Test suite for get_row method."""

    @pytest.mark.asyncio
    async def test_get_row_retrieves_by_id(self, monkeypatch):
        """Should retrieve row by ID and return data."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = ZeroDBService()

        mock_response = {
            "id": "row_123",
            "name": "Test Product",
            "price": 24.99
        }

        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await service.get_row("products", "row_123")

            assert result == mock_response
            args = mock_request.call_args
            assert args[0][0] == "GET"
            assert "/tables/products/rows/row_123" in args[0][1]

    @pytest.mark.asyncio
    async def test_get_row_handles_not_found_error(self, monkeypatch):
        """Should raise ZeroDBNotFoundError when row doesn't exist."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = ZeroDBService()

        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = ZeroDBNotFoundError("Resource not found")

            with pytest.raises(ZeroDBNotFoundError):
                await service.get_row("products", "nonexistent_id")

    @pytest.mark.asyncio
    async def test_get_row_raises_error_for_empty_table_name(self, monkeypatch):
        """Should raise ZeroDBValidationError for empty table name."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = ZeroDBService()

        with pytest.raises(ZeroDBValidationError) as exc_info:
            await service.get_row("", "row_123")
        assert "Table name is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_row_raises_error_for_empty_row_id(self, monkeypatch):
        """Should raise ZeroDBValidationError for empty row ID."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = ZeroDBService()

        with pytest.raises(ZeroDBValidationError) as exc_info:
            await service.get_row("products", "")
        assert "Row ID is required" in str(exc_info.value)


class TestZeroDBServiceQueryRows:
    """Test suite for query_rows method."""

    @pytest.mark.asyncio
    async def test_query_rows_with_filter(self, monkeypatch):
        """Should query rows with MongoDB-style filter."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = ZeroDBService()

        mock_response = {
            "results": [
                {"id": "row_1", "name": "Product 1", "price": 29.99},
                {"id": "row_2", "name": "Product 2", "price": 39.99}
            ],
            "total": 2,
            "limit": 100,
            "skip": 0
        }

        filter_query = {"price": {"$gte": 20}, "is_active": True}

        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await service.query_rows("products", filter=filter_query)

            assert result == mock_response
            args = mock_request.call_args
            assert args[0][0] == "POST"
            assert "/tables/products/query" in args[0][1]
            assert args[1]["json_data"]["filter"] == filter_query

    @pytest.mark.asyncio
    async def test_query_rows_with_pagination(self, monkeypatch):
        """Should support pagination with limit and skip."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = ZeroDBService()

        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"results": [], "total": 0}

            await service.query_rows("products", limit=50, skip=100)

            args = mock_request.call_args
            payload = args[1]["json_data"]
            assert payload["limit"] == 50
            assert payload["skip"] == 100

    @pytest.mark.asyncio
    async def test_query_rows_with_sort(self, monkeypatch):
        """Should support sorting with MongoDB-style sort spec."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = ZeroDBService()

        sort_spec = {"created_at": -1, "name": 1}

        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"results": [], "total": 0}

            await service.query_rows("products", sort=sort_spec)

            args = mock_request.call_args
            payload = args[1]["json_data"]
            assert payload["sort"] == sort_spec

    @pytest.mark.asyncio
    async def test_query_rows_without_filter(self, monkeypatch):
        """Should query all rows when no filter is provided."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = ZeroDBService()

        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"results": [], "total": 0}

            await service.query_rows("products")

            args = mock_request.call_args
            payload = args[1]["json_data"]
            assert payload["filter"] == {}

    @pytest.mark.asyncio
    async def test_query_rows_raises_error_for_empty_table_name(self, monkeypatch):
        """Should raise ZeroDBValidationError for empty table name."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = ZeroDBService()

        with pytest.raises(ZeroDBValidationError) as exc_info:
            await service.query_rows("")
        assert "Table name is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_query_rows_raises_error_for_invalid_limit(self, monkeypatch):
        """Should raise ZeroDBValidationError for limit < 1."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = ZeroDBService()

        with pytest.raises(ZeroDBValidationError) as exc_info:
            await service.query_rows("products", limit=0)
        assert "Limit must be greater than 0" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_query_rows_raises_error_for_negative_skip(self, monkeypatch):
        """Should raise ZeroDBValidationError for negative skip."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = ZeroDBService()

        with pytest.raises(ZeroDBValidationError) as exc_info:
            await service.query_rows("products", skip=-1)
        assert "Skip must be non-negative" in str(exc_info.value)


class TestZeroDBServiceUpdateRow:
    """Test suite for update_row method."""

    @pytest.mark.asyncio
    async def test_update_row_with_new_data(self, monkeypatch):
        """Should update row and return updated data."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = ZeroDBService()

        mock_response = {
            "id": "row_123",
            "name": "Updated Product",
            "price": 29.99,
            "updated_at": "2026-01-02T00:00:00Z"
        }

        update_data = {"name": "Updated Product", "price": 29.99}

        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await service.update_row("products", "row_123", update_data)

            assert result == mock_response
            args = mock_request.call_args
            assert args[0][0] == "PUT"
            assert "/tables/products/rows/row_123" in args[0][1]
            assert args[1]["json_data"] == update_data

    @pytest.mark.asyncio
    async def test_update_row_raises_error_for_empty_table_name(self, monkeypatch):
        """Should raise ZeroDBValidationError for empty table name."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = ZeroDBService()

        with pytest.raises(ZeroDBValidationError) as exc_info:
            await service.update_row("", "row_123", {"name": "Updated"})
        assert "Table name is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_row_raises_error_for_empty_row_id(self, monkeypatch):
        """Should raise ZeroDBValidationError for empty row ID."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = ZeroDBService()

        with pytest.raises(ZeroDBValidationError) as exc_info:
            await service.update_row("products", "", {"name": "Updated"})
        assert "Row ID is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_row_raises_error_for_empty_data(self, monkeypatch):
        """Should raise ZeroDBValidationError for empty update data."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = ZeroDBService()

        with pytest.raises(ZeroDBValidationError) as exc_info:
            await service.update_row("products", "row_123", {})
        assert "Data is required for row update" in str(exc_info.value)


class TestZeroDBServiceDeleteRow:
    """Test suite for delete_row method."""

    @pytest.mark.asyncio
    async def test_delete_row_by_id(self, monkeypatch):
        """Should delete row and return confirmation."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = ZeroDBService()

        mock_response = {"deleted": True, "id": "row_123"}

        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await service.delete_row("products", "row_123")

            assert result == mock_response
            args = mock_request.call_args
            assert args[0][0] == "DELETE"
            assert "/tables/products/rows/row_123" in args[0][1]

    @pytest.mark.asyncio
    async def test_delete_row_raises_error_for_empty_table_name(self, monkeypatch):
        """Should raise ZeroDBValidationError for empty table name."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = ZeroDBService()

        with pytest.raises(ZeroDBValidationError) as exc_info:
            await service.delete_row("", "row_123")
        assert "Table name is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_row_raises_error_for_empty_row_id(self, monkeypatch):
        """Should raise ZeroDBValidationError for empty row ID."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = ZeroDBService()

        with pytest.raises(ZeroDBValidationError) as exc_info:
            await service.delete_row("products", "")
        assert "Row ID is required" in str(exc_info.value)


class TestZeroDBServiceListTables:
    """Test suite for list_tables method."""

    @pytest.mark.asyncio
    async def test_list_all_tables(self, monkeypatch):
        """Should retrieve list of all tables in project."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = ZeroDBService()

        mock_response = {
            "tables": [
                {"name": "products", "schema": {}, "indexes": []},
                {"name": "orders", "schema": {}, "indexes": []},
                {"name": "sessions", "schema": {}, "indexes": []}
            ]
        }

        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await service.list_tables()

            assert len(result) == 3
            assert result[0]["name"] == "products"
            assert result[1]["name"] == "orders"
            args = mock_request.call_args
            assert args[0][0] == "GET"
            assert "/tables" in args[0][1]

    @pytest.mark.asyncio
    async def test_list_tables_returns_empty_list_when_no_tables(self, monkeypatch):
        """Should return empty list when no tables exist."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = ZeroDBService()

        with patch.object(service, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"tables": []}

            result = await service.list_tables()

            assert result == []


class TestZeroDBServiceRetryLogic:
    """Test suite for retry logic with exponential backoff."""

    @pytest.mark.asyncio
    async def test_retries_on_timeout_error(self, monkeypatch):
        """Should retry request on timeout with exponential backoff."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = ZeroDBService(max_retries=2, timeout=1)

        call_count = 0

        async def mock_client_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.TimeoutException("Request timeout")
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": "row_123"}
            return mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get = mock_client_request
            mock_client_class.return_value = mock_client

            result = await service.get_row("products", "row_123")
            assert result["id"] == "row_123"
            assert call_count == 3

    @pytest.mark.asyncio
    async def test_raises_connection_error_after_max_retries(self, monkeypatch):
        """Should raise ZeroDBConnectionError after max retries exceeded."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = ZeroDBService(max_retries=2, timeout=1)

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get.side_effect = httpx.TimeoutException("Request timeout")
            mock_client_class.return_value = mock_client

            with pytest.raises(ZeroDBConnectionError) as exc_info:
                await service.get_row("products", "row_123")
            assert "after 2 retries" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_retries_on_connection_error(self, monkeypatch):
        """Should retry request on connection error."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = ZeroDBService(max_retries=2, timeout=1)

        call_count = 0

        async def mock_client_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise httpx.ConnectError("Connection failed")
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": "row_123"}
            return mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.get = mock_client_request
            mock_client_class.return_value = mock_client

            result = await service.get_row("products", "row_123")
            assert result["id"] == "row_123"
            assert call_count == 2


class TestZeroDBServiceErrorHandling:
    """Test suite for HTTP error handling."""

    @pytest.mark.asyncio
    async def test_raises_not_found_error_for_404(self, monkeypatch):
        """Should raise ZeroDBNotFoundError for 404 status."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = ZeroDBService()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_response = Mock()
            mock_response.status_code = 404
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            with pytest.raises(ZeroDBNotFoundError):
                await service.get_row("products", "nonexistent_id")

    @pytest.mark.asyncio
    async def test_raises_validation_error_for_400(self, monkeypatch):
        """Should raise ZeroDBValidationError for 400 status."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = ZeroDBService()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {"detail": "Invalid data"}
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            with pytest.raises(ZeroDBValidationError) as exc_info:
                await service.create_row("products", {"name": ""})
            assert "Invalid data" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_raises_http_exception_for_other_errors(self, monkeypatch):
        """Should raise HTTPException for other HTTP errors."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = ZeroDBService()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal server error"
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Server error", request=Mock(), response=mock_response
            )
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            with pytest.raises(HTTPException) as exc_info:
                await service.get_row("products", "row_123")
            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_does_not_retry_validation_errors(self, monkeypatch):
        """Should not retry on validation errors (400)."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = ZeroDBService(max_retries=3)

        call_count = 0

        async def mock_client_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {"detail": "Bad request"}
            return mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post = mock_client_request
            mock_client_class.return_value = mock_client

            with pytest.raises(ZeroDBValidationError):
                await service.create_row("products", {"name": ""})
            assert call_count == 1


class TestGetZeroDBServiceFunction:
    """Test suite for get_zerodb_service dependency injection helper."""

    def test_returns_configured_service_instance(self, monkeypatch):
        """Should return configured ZeroDBService instance."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = get_zerodb_service()

        assert isinstance(service, ZeroDBService)
        assert service.project_id == "proj_test_123"
