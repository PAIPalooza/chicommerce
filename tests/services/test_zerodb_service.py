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


class TestGetZeroDBServiceFunction:
    """Test suite for get_zerodb_service dependency injection helper."""

    def test_returns_configured_service_instance(self, monkeypatch):
        """Should return configured ZeroDBService instance."""
        monkeypatch.setattr(settings, "ZERODB_PROJECT_ID", "proj_test_123")
        monkeypatch.setattr(settings, "AINATIVE_API_TOKEN", "test_token")

        service = get_zerodb_service()

        assert isinstance(service, ZeroDBService)
        assert service.project_id == "proj_test_123"
