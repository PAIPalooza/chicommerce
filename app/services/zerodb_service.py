"""
ZeroDB service for database operations.

This module provides a comprehensive service layer for interacting with ZeroDB API,
including all CRUD operations, error handling, and retry logic.
"""
import asyncio
import httpx
from typing import Optional, Dict, List, Any
from fastapi import HTTPException, status
from app.core.config import settings


class ZeroDBError(Exception):
    """Base exception for ZeroDB service errors."""
    pass


class ZeroDBConnectionError(ZeroDBError):
    """Exception raised when connection to ZeroDB fails."""
    pass


class ZeroDBNotFoundError(ZeroDBError):
    """Exception raised when a resource is not found in ZeroDB."""
    pass


class ZeroDBValidationError(ZeroDBError):
    """Exception raised when validation fails for ZeroDB operations."""
    pass


class ZeroDBService:
    """Service for interacting with ZeroDB API."""

    def __init__(
        self,
        project_id: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None
    ):
        """
        Initialize ZeroDB service.

        Args:
            project_id: ZeroDB project ID (defaults to settings)
            timeout: Request timeout in seconds (defaults to settings)
            max_retries: Maximum retry attempts (defaults to settings)

        Raises:
            ZeroDBValidationError: If required configuration is missing
        """
        self.project_id = project_id or settings.ZERODB_PROJECT_ID
        self.timeout = timeout or settings.ZERODB_TIMEOUT
        self.max_retries = max_retries or settings.ZERODB_MAX_RETRIES

        if not self.project_id:
            raise ZeroDBValidationError("ZERODB_PROJECT_ID is required")

        if not settings.AINATIVE_API_TOKEN:
            raise ZeroDBValidationError("AINATIVE_API_TOKEN is required")

        self.base_url = f"{settings.AINATIVE_API_URL}v1/public/zerodb/{self.project_id}/database"
        self.headers = {
            "Authorization": f"Bearer {settings.AINATIVE_API_TOKEN}",
            "Content-Type": "application/json"
        }

    async def _make_request(
        self,
        method: str,
        url: str,
        json_data: Optional[Dict[str, Any]] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Make an HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: Request URL
            json_data: JSON payload for POST/PUT requests
            retry_count: Current retry attempt number

        Returns:
            Response JSON data

        Raises:
            ZeroDBConnectionError: If connection fails after retries
            ZeroDBNotFoundError: If resource is not found (404)
            HTTPException: For other HTTP errors
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(url, headers=self.headers)
                elif method.upper() == "POST":
                    response = await client.post(url, json=json_data, headers=self.headers)
                elif method.upper() == "PUT":
                    response = await client.put(url, json=json_data, headers=self.headers)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=self.headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                # Handle specific HTTP status codes
                if response.status_code == 404:
                    raise ZeroDBNotFoundError(f"Resource not found: {url}")

                if response.status_code == 400:
                    error_detail = response.json().get("detail", "Bad request")
                    raise ZeroDBValidationError(f"Validation error: {error_detail}")

                # Raise for other HTTP errors
                response.raise_for_status()

                # Return JSON response
                return response.json()

        except httpx.TimeoutException as e:
            if retry_count < self.max_retries:
                # Exponential backoff: 1s, 2s, 4s
                wait_time = 2 ** retry_count
                await asyncio.sleep(wait_time)
                return await self._make_request(method, url, json_data, retry_count + 1)
            raise ZeroDBConnectionError(f"Request timeout after {self.max_retries} retries: {str(e)}")

        except httpx.ConnectError as e:
            if retry_count < self.max_retries:
                wait_time = 2 ** retry_count
                await asyncio.sleep(wait_time)
                return await self._make_request(method, url, json_data, retry_count + 1)
            raise ZeroDBConnectionError(f"Connection failed after {self.max_retries} retries: {str(e)}")

        except (ZeroDBNotFoundError, ZeroDBValidationError):
            # Don't retry for these errors
            raise

        except httpx.HTTPStatusError as e:
            # Convert to FastAPI HTTPException
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"ZeroDB API error: {e.response.text}"
            )

    async def create_row(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new row in a table.

        Args:
            table: Table name
            data: Row data to insert

        Returns:
            Created row data including generated ID

        Raises:
            ZeroDBValidationError: If table name or data is invalid
            ZeroDBConnectionError: If connection fails
            HTTPException: For other API errors

        Example:
            >>> zerodb = ZeroDBService()
            >>> product = await zerodb.create_row("products", {
            ...     "name": "T-Shirt",
            ...     "price": 24.99,
            ...     "is_active": True
            ... })
            >>> print(product["id"])
        """
        if not table:
            raise ZeroDBValidationError("Table name is required")

        if not data:
            raise ZeroDBValidationError("Data is required for row creation")

        url = f"{self.base_url}/tables/{table}/rows"
        return await self._make_request("POST", url, json_data=data)

    async def get_row(self, table: str, row_id: str) -> Dict[str, Any]:
        """
        Get a row by ID.

        Args:
            table: Table name
            row_id: Row ID

        Returns:
            Row data

        Raises:
            ZeroDBValidationError: If table name or row_id is invalid
            ZeroDBNotFoundError: If row is not found
            ZeroDBConnectionError: If connection fails
            HTTPException: For other API errors

        Example:
            >>> zerodb = ZeroDBService()
            >>> product = await zerodb.get_row("products", "prod_123")
            >>> print(product["name"])
        """
        if not table:
            raise ZeroDBValidationError("Table name is required")

        if not row_id:
            raise ZeroDBValidationError("Row ID is required")

        url = f"{self.base_url}/tables/{table}/rows/{row_id}"
        return await self._make_request("GET", url)

    async def query_rows(
        self,
        table: str,
        filter: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        skip: int = 0,
        sort: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """
        Query rows with filters (MongoDB-style).

        Args:
            table: Table name
            filter: MongoDB-style filter (e.g., {"price": {"$gte": 10}})
            limit: Maximum number of results (default: 100)
            skip: Number of results to skip for pagination (default: 0)
            sort: Sort specification (e.g., {"created_at": -1})

        Returns:
            Query results with metadata:
            {
                "results": [...],
                "total": 100,
                "limit": 100,
                "skip": 0
            }

        Raises:
            ZeroDBValidationError: If table name is invalid
            ZeroDBConnectionError: If connection fails
            HTTPException: For other API errors

        Example:
            >>> zerodb = ZeroDBService()
            >>> # Query active products priced >= $20
            >>> results = await zerodb.query_rows(
            ...     "products",
            ...     filter={"is_active": True, "price": {"$gte": 20}},
            ...     limit=50,
            ...     sort={"created_at": -1}
            ... )
            >>> print(f"Found {results['total']} products")
        """
        if not table:
            raise ZeroDBValidationError("Table name is required")

        if limit < 1:
            raise ZeroDBValidationError("Limit must be greater than 0")

        if skip < 0:
            raise ZeroDBValidationError("Skip must be non-negative")

        url = f"{self.base_url}/tables/{table}/query"

        payload = {
            "filter": filter or {},
            "limit": limit,
            "skip": skip
        }

        if sort:
            payload["sort"] = sort

        return await self._make_request("POST", url, json_data=payload)

    async def update_row(
        self,
        table: str,
        row_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a row.

        Args:
            table: Table name
            row_id: Row ID
            data: Updated field values

        Returns:
            Updated row data

        Raises:
            ZeroDBValidationError: If table name, row_id, or data is invalid
            ZeroDBNotFoundError: If row is not found
            ZeroDBConnectionError: If connection fails
            HTTPException: For other API errors

        Example:
            >>> zerodb = ZeroDBService()
            >>> updated = await zerodb.update_row(
            ...     "products",
            ...     "prod_123",
            ...     {"price": 29.99, "is_active": True}
            ... )
            >>> print(updated["price"])
        """
        if not table:
            raise ZeroDBValidationError("Table name is required")

        if not row_id:
            raise ZeroDBValidationError("Row ID is required")

        if not data:
            raise ZeroDBValidationError("Data is required for row update")

        url = f"{self.base_url}/tables/{table}/rows/{row_id}"
        return await self._make_request("PUT", url, json_data=data)

    async def delete_row(self, table: str, row_id: str) -> Dict[str, Any]:
        """
        Delete a row.

        Args:
            table: Table name
            row_id: Row ID

        Returns:
            Deletion confirmation:
            {
                "deleted": True,
                "id": "row_id"
            }

        Raises:
            ZeroDBValidationError: If table name or row_id is invalid
            ZeroDBNotFoundError: If row is not found
            ZeroDBConnectionError: If connection fails
            HTTPException: For other API errors

        Example:
            >>> zerodb = ZeroDBService()
            >>> result = await zerodb.delete_row("products", "prod_123")
            >>> print(result["deleted"])
        """
        if not table:
            raise ZeroDBValidationError("Table name is required")

        if not row_id:
            raise ZeroDBValidationError("Row ID is required")

        url = f"{self.base_url}/tables/{table}/rows/{row_id}"
        return await self._make_request("DELETE", url)

    async def list_tables(self) -> List[Dict[str, Any]]:
        """
        List all tables in the project.

        Returns:
            List of table metadata:
            [
                {
                    "name": "products",
                    "schema": {...},
                    "indexes": [...],
                    "created_at": "2026-01-01T00:00:00Z"
                },
                ...
            ]

        Raises:
            ZeroDBConnectionError: If connection fails
            HTTPException: For other API errors

        Example:
            >>> zerodb = ZeroDBService()
            >>> tables = await zerodb.list_tables()
            >>> for table in tables:
            ...     print(f"Table: {table['name']}")
        """
        url = f"{self.base_url}/tables"
        response = await self._make_request("GET", url)
        return response.get("tables", [])


def get_zerodb_service() -> ZeroDBService:
    """
    Dependency injection helper for FastAPI endpoints.

    Returns:
        Configured ZeroDBService instance

    Example:
        >>> from fastapi import Depends
        >>>
        >>> @app.get("/products")
        >>> async def list_products(
        ...     zerodb: ZeroDBService = Depends(get_zerodb_service)
        ... ):
        ...     results = await zerodb.query_rows("products")
        ...     return results
    """
    return ZeroDBService()
