from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, ConfigDict, Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # CORS
    CORS_ORIGINS: List[AnyHttpUrl] = []

    # Database
    DATABASE_URL: PostgresDsn
    TEST_DATABASE_URL: PostgresDsn
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Admin
    ADMIN_API_KEY: str

    # Payment webhooks
    STRIPE_WEBHOOK_SECRET: str = "test_stripe_webhook_secret"
    PAYPAL_WEBHOOK_ID: str = "test_paypal_webhook_id"

    # Logging
    LOG_LEVEL: str = "INFO"

    # Celery/Background Tasks
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # AINative Authentication
    AINATIVE_API_URL: str = "https://api.ainative.studio/"
    AINATIVE_API_TOKEN: str
    AINATIVE_USERNAME: Optional[str] = None
    AINATIVE_PASSWORD: Optional[str] = None

    # ZeroDB
    ZERODB_PROJECT_ID: Optional[str] = None
    ZERODB_HOST: Optional[str] = None
    ZERODB_PORT: Optional[int] = None
    ZERODB_DATABASE: Optional[str] = None
    ZERODB_USERNAME: Optional[str] = None
    ZERODB_PASSWORD: Optional[str] = None
    ZERODB_URL: Optional[str] = None
    ZERODB_TIMEOUT: int = 30  # Request timeout in seconds
    ZERODB_MAX_RETRIES: int = 3  # Maximum retry attempts

    # S3 Storage Configuration
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "zerocommerce-previews"
    S3_ENDPOINT_URL: Optional[str] = None  # For local testing with MinIO/LocalStack

    # Preview Settings
    PREVIEW_STORAGE_TYPE: str = "s3"  # Options: "s3", "local"
    PREVIEW_LOCAL_PATH: str = "./storage/previews"  # For local development
    PREVIEW_EXPIRY_SECONDS: int = 3600  # 1 hour for signed URLs

    # Security Settings
    TLS_ENABLED: bool = True  # Enable TLS/HTTPS enforcement
    HTTPS_REDIRECT_ENABLED: bool = True  # Enable automatic HTTP to HTTPS redirect
    SECURITY_HEADERS_ENABLED: bool = True  # Enable security headers middleware
    HSTS_MAX_AGE: int = 31536000  # HSTS max-age in seconds (1 year)
    HSTS_INCLUDE_SUBDOMAINS: bool = True  # Include subdomains in HSTS
    HSTS_PRELOAD: bool = False  # Enable HSTS preload (requires submission to browser vendors)

    @field_validator("CORS_ORIGINS", mode='before')
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        elif isinstance(v, str):
            return [v.strip()]
        raise ValueError("CORS_ORIGINS must be a string or list of strings")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        case_sensitive=True,
        extra='ignore'  # Ignore extra fields in .env file
    )


settings = Settings()
