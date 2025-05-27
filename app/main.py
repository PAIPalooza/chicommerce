"""
Main FastAPI application.
"""
import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.api.v1.api import api_router
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ChiCommerce API",
    description="eCommerce API for customized products",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom error handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Custom handler for validation errors to format responses according to our standards.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": exc.body,
        },
    )

# Include API router with the correct prefix
app.include_router(api_router, prefix=settings.API_V1_STR)

# Add a test endpoint to verify the API is working
@app.get(f"{settings.API_V1_STR}/test")
async def test_endpoint():
    return {"message": "API is working!"}

# Health check endpoint
@app.get("/health", tags=["health"])
def health_check() -> Any:
    """
    Health check endpoint.
    """
    return {"status": "ok"}

# Root endpoint
@app.get("/", tags=["root"])
def root() -> Any:
    """
    Root endpoint with API information.
    """
    return {
        "name": "ChiCommerce API",
        "version": "0.1.0",
        "docs": "/api/docs",
    }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
