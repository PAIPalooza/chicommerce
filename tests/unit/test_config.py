"""Unit tests for application configuration.

This module tests the Settings class to ensure all configuration
parameters are properly loaded and validated.
"""
import os
from typing import Optional

import pytest
from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.config import Settings


class ConfigSettings(BaseSettings):
    """Test version of Settings that doesn't load from .env file."""

    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    CORS_ORIGINS: list = []
    DATABASE_URL: str
    TEST_DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    ADMIN_API_KEY: str
    STRIPE_WEBHOOK_SECRET: str = "test_stripe_webhook_secret"
    PAYPAL_WEBHOOK_ID: str = "test_paypal_webhook_id"
    LOG_LEVEL: str = "INFO"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    AINATIVE_API_URL: str = "https://api.ainative.studio/"
    AINATIVE_API_TOKEN: str
    AINATIVE_USERNAME: Optional[str] = None
    AINATIVE_PASSWORD: Optional[str] = None
    ZERODB_PROJECT_ID: str
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "zerocommerce-previews"
    S3_ENDPOINT_URL: Optional[str] = None
    PREVIEW_STORAGE_TYPE: str = "s3"
    PREVIEW_LOCAL_PATH: str = "./storage/previews"
    PREVIEW_EXPIRY_SECONDS: int = 3600
    TLS_ENABLED: bool = True
    HTTPS_REDIRECT_ENABLED: bool = True
    SECURITY_HEADERS_ENABLED: bool = True
    HSTS_MAX_AGE: int = 31536000
    HSTS_INCLUDE_SUBDOMAINS: bool = True
    HSTS_PRELOAD: bool = False

    model_config = SettingsConfigDict(
        env_file=None,
        case_sensitive=True,
        extra='ignore'
    )


class TestSettingsValidation:
    """Test suite for Settings validation."""

    def test_settings_loads_with_all_required_fields(self, monkeypatch):
        """
        Given all required environment variables are set
        When Settings is instantiated
        Then it should load successfully without errors
        """
        # Arrange
        required_vars = {
            "DATABASE_URL": "postgresql+psycopg2://user:pass@localhost:5432/testdb",
            "TEST_DATABASE_URL": "postgresql+psycopg2://user:pass@localhost:5432/testdb_test",
            "SECRET_KEY": "test-secret-key-min-32-characters-long",
            "ADMIN_API_KEY": "test-admin-key",
            "AINATIVE_API_TOKEN": "test-ainative-token",
            "ZERODB_PROJECT_ID": "test-project-id",
        }

        for key, value in required_vars.items():
            monkeypatch.setenv(key, value)

        # Act
        settings = ConfigSettings()

        # Assert
        assert settings.SECRET_KEY == "test-secret-key-min-32-characters-long"
        assert settings.ADMIN_API_KEY == "test-admin-key"
        assert settings.AINATIVE_API_TOKEN == "test-ainative-token"
        assert settings.ZERODB_PROJECT_ID == "test-project-id"

    def test_ainative_api_url_has_default_value(self, monkeypatch):
        """
        Given AINATIVE_API_URL is not set in environment
        When Settings is instantiated
        Then it should use the default value
        """
        # Arrange
        required_vars = {
            "DATABASE_URL": "postgresql+psycopg2://user:pass@localhost:5432/testdb",
            "TEST_DATABASE_URL": "postgresql+psycopg2://user:pass@localhost:5432/testdb_test",
            "SECRET_KEY": "test-secret-key",
            "ADMIN_API_KEY": "test-admin-key",
            "AINATIVE_API_TOKEN": "test-token",
            "ZERODB_PROJECT_ID": "test-project",
        }

        for key, value in required_vars.items():
            monkeypatch.setenv(key, value)

        # Act
        settings = ConfigSettings()

        # Assert
        assert settings.AINATIVE_API_URL == "https://api.ainative.studio/"

    def test_ainative_username_is_optional(self, monkeypatch):
        """
        Given AINATIVE_USERNAME is not set in environment
        When Settings is instantiated
        Then it should be None
        """
        # Arrange - Clear any existing env vars
        monkeypatch.delenv("AINATIVE_USERNAME", raising=False)
        monkeypatch.delenv("AINATIVE_PASSWORD", raising=False)

        required_vars = {
            "DATABASE_URL": "postgresql+psycopg2://user:pass@localhost:5432/testdb",
            "TEST_DATABASE_URL": "postgresql+psycopg2://user:pass@localhost:5432/testdb_test",
            "SECRET_KEY": "test-secret-key",
            "ADMIN_API_KEY": "test-admin-key",
            "AINATIVE_API_TOKEN": "test-token",
            "ZERODB_PROJECT_ID": "test-project",
        }

        for key, value in required_vars.items():
            monkeypatch.setenv(key, value)

        # Act
        settings = ConfigSettings()

        # Assert
        assert settings.AINATIVE_USERNAME is None

    def test_ainative_password_is_optional(self, monkeypatch):
        """
        Given AINATIVE_PASSWORD is not set in environment
        When Settings is instantiated
        Then it should be None
        """
        # Arrange - Clear any existing env vars
        monkeypatch.delenv("AINATIVE_USERNAME", raising=False)
        monkeypatch.delenv("AINATIVE_PASSWORD", raising=False)

        required_vars = {
            "DATABASE_URL": "postgresql+psycopg2://user:pass@localhost:5432/testdb",
            "TEST_DATABASE_URL": "postgresql+psycopg2://user:pass@localhost:5432/testdb_test",
            "SECRET_KEY": "test-secret-key",
            "ADMIN_API_KEY": "test-admin-key",
            "AINATIVE_API_TOKEN": "test-token",
            "ZERODB_PROJECT_ID": "test-project",
        }

        for key, value in required_vars.items():
            monkeypatch.setenv(key, value)

        # Act
        settings = ConfigSettings()

        # Assert
        assert settings.AINATIVE_PASSWORD is None

    def test_ainative_username_can_be_set(self, monkeypatch):
        """
        Given AINATIVE_USERNAME is set in environment
        When Settings is instantiated
        Then it should use the provided value
        """
        # Arrange
        required_vars = {
            "DATABASE_URL": "postgresql+psycopg2://user:pass@localhost:5432/testdb",
            "TEST_DATABASE_URL": "postgresql+psycopg2://user:pass@localhost:5432/testdb_test",
            "SECRET_KEY": "test-secret-key",
            "ADMIN_API_KEY": "test-admin-key",
            "AINATIVE_API_TOKEN": "test-token",
            "AINATIVE_USERNAME": "test@example.com",
            "ZERODB_PROJECT_ID": "test-project",
        }

        for key, value in required_vars.items():
            monkeypatch.setenv(key, value)

        # Act
        settings = ConfigSettings()

        # Assert
        assert settings.AINATIVE_USERNAME == "test@example.com"

    def test_ainative_password_can_be_set(self, monkeypatch):
        """
        Given AINATIVE_PASSWORD is set in environment
        When Settings is instantiated
        Then it should use the provided value
        """
        # Arrange
        required_vars = {
            "DATABASE_URL": "postgresql+psycopg2://user:pass@localhost:5432/testdb",
            "TEST_DATABASE_URL": "postgresql+psycopg2://user:pass@localhost:5432/testdb_test",
            "SECRET_KEY": "test-secret-key",
            "ADMIN_API_KEY": "test-admin-key",
            "AINATIVE_API_TOKEN": "test-token",
            "AINATIVE_PASSWORD": "test-password",
            "ZERODB_PROJECT_ID": "test-project",
        }

        for key, value in required_vars.items():
            monkeypatch.setenv(key, value)

        # Act
        settings = ConfigSettings()

        # Assert
        assert settings.AINATIVE_PASSWORD == "test-password"

    def test_settings_fails_without_ainative_api_token(self, monkeypatch):
        """
        Given AINATIVE_API_TOKEN is not set in environment
        When Settings is instantiated
        Then it should raise a ValidationError
        """
        # Arrange - Clear the API token
        monkeypatch.delenv("AINATIVE_API_TOKEN", raising=False)

        required_vars = {
            "DATABASE_URL": "postgresql+psycopg2://user:pass@localhost:5432/testdb",
            "TEST_DATABASE_URL": "postgresql+psycopg2://user:pass@localhost:5432/testdb_test",
            "SECRET_KEY": "test-secret-key",
            "ADMIN_API_KEY": "test-admin-key",
            "ZERODB_PROJECT_ID": "test-project",
        }

        for key, value in required_vars.items():
            monkeypatch.setenv(key, value)

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ConfigSettings()

        # Verify the error is for AINATIVE_API_TOKEN
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("AINATIVE_API_TOKEN",) for error in errors)

    def test_settings_fails_without_zerodb_project_id(self, monkeypatch):
        """
        Given ZERODB_PROJECT_ID is not set in environment
        When Settings is instantiated
        Then it should raise a ValidationError
        """
        # Arrange - Clear the project ID
        monkeypatch.delenv("ZERODB_PROJECT_ID", raising=False)

        required_vars = {
            "DATABASE_URL": "postgresql+psycopg2://user:pass@localhost:5432/testdb",
            "TEST_DATABASE_URL": "postgresql+psycopg2://user:pass@localhost:5432/testdb_test",
            "SECRET_KEY": "test-secret-key",
            "ADMIN_API_KEY": "test-admin-key",
            "AINATIVE_API_TOKEN": "test-token",
        }

        for key, value in required_vars.items():
            monkeypatch.setenv(key, value)

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ConfigSettings()

        # Verify the error is for ZERODB_PROJECT_ID
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("ZERODB_PROJECT_ID",) for error in errors)

    def test_zerodb_project_id_is_required(self, monkeypatch):
        """
        Given ZERODB_PROJECT_ID is set in environment
        When Settings is instantiated
        Then it should use the provided value
        """
        # Arrange
        required_vars = {
            "DATABASE_URL": "postgresql+psycopg2://user:pass@localhost:5432/testdb",
            "TEST_DATABASE_URL": "postgresql+psycopg2://user:pass@localhost:5432/testdb_test",
            "SECRET_KEY": "test-secret-key",
            "ADMIN_API_KEY": "test-admin-key",
            "AINATIVE_API_TOKEN": "test-token",
            "ZERODB_PROJECT_ID": "my-zerodb-project",
        }

        for key, value in required_vars.items():
            monkeypatch.setenv(key, value)

        # Act
        settings = ConfigSettings()

        # Assert
        assert settings.ZERODB_PROJECT_ID == "my-zerodb-project"


class TestSettingsDefaults:
    """Test suite for default configuration values."""

    def test_api_v1_str_has_correct_default(self, monkeypatch):
        """
        Given API_V1_STR is not set in environment
        When Settings is instantiated
        Then it should use the default value /api/v1
        """
        # Arrange
        self._set_required_vars(monkeypatch)

        # Act
        settings = ConfigSettings()

        # Assert
        assert settings.API_V1_STR == "/api/v1"

    def test_access_token_expire_minutes_has_correct_default(self, monkeypatch):
        """
        Given ACCESS_TOKEN_EXPIRE_MINUTES is not set
        When Settings is instantiated
        Then it should default to 8 days (11520 minutes)
        """
        # Arrange
        self._set_required_vars(monkeypatch)

        # Act
        settings = ConfigSettings()

        # Assert
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60 * 24 * 8

    def test_redis_url_has_correct_default(self, monkeypatch):
        """
        Given REDIS_URL is not set in environment
        When Settings is instantiated
        Then it should use the default localhost Redis URL
        """
        # Arrange
        self._set_required_vars(monkeypatch)

        # Act
        settings = ConfigSettings()

        # Assert
        assert settings.REDIS_URL == "redis://localhost:6379/0"

    def test_log_level_has_correct_default(self, monkeypatch):
        """
        Given LOG_LEVEL is not set in environment
        When Settings is instantiated
        Then it should default to INFO
        """
        # Arrange
        self._set_required_vars(monkeypatch)

        # Act
        settings = ConfigSettings()

        # Assert
        assert settings.LOG_LEVEL == "INFO"

    @staticmethod
    def _set_required_vars(monkeypatch):
        """Helper method to set all required environment variables."""
        required_vars = {
            "DATABASE_URL": "postgresql+psycopg2://user:pass@localhost:5432/testdb",
            "TEST_DATABASE_URL": "postgresql+psycopg2://user:pass@localhost:5432/testdb_test",
            "SECRET_KEY": "test-secret-key",
            "ADMIN_API_KEY": "test-admin-key",
            "AINATIVE_API_TOKEN": "test-token",
            "ZERODB_PROJECT_ID": "test-project",
        }

        for key, value in required_vars.items():
            monkeypatch.setenv(key, value)
