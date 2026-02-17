# ZeroDB Migration - Quick Start Guide

**Version:** 1.0
**Date:** 2026-02-16

This guide provides step-by-step instructions for implementing ZeroDB and AINative authentication in ZeroCommerce.

---

## Prerequisites

- [ ] AINative account credentials
- [ ] Python 3.11+
- [ ] Existing ZeroCommerce installation

---

## Step 1: Update Environment Configuration

### 1.1 Update `.env`

Add these credentials to your `.env` file:

```bash
# AINative Authentication
AINATIVE_USERNAME=admin@ainative.studio
AINATIVE_PASSWORD=Admin2025!Secure
AINATIVE_API_URL=https://api.ainative.studio/
AINATIVE_API_TOKEN=kLPiP0bzgKJ0CnNYVt1wq3qxbs2QgDeF2XwyUnxBEOM

# ZeroDB Project (you'll get this from Step 2)
ZERODB_PROJECT_ID=proj_your_project_id_here
```

### 1.2 Install New Dependencies

Add to `requirements.txt`:

```txt
httpx>=0.27.0
python-jose[cryptography]>=3.3.0
python-multipart>=0.0.6
```

Install:

```bash
pip install -r requirements.txt
```

---

## Step 2: Create ZeroDB Project

### 2.1 Test AINative Connection

Create `scripts/test_ainative_connection.py`:

```python
import asyncio
import httpx

AINATIVE_API_URL = "https://api.ainative.studio/"
AINATIVE_API_TOKEN = "kLPiP0bzgKJ0CnNYVt1wq3qxbs2QgDeF2XwyUnxBEOM"

async def test_connection():
    """Test AINative API connection."""
    url = f"{AINATIVE_API_URL}v1/public/projects"
    headers = {"Authorization": f"Bearer {AINATIVE_API_TOKEN}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

    if response.status_code == 200:
        print("✅ Successfully connected to AINative API")
        print(f"Response: {response.json()}")
    else:
        print(f"❌ Connection failed: {response.status_code}")
        print(f"Error: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_connection())
```

Run:

```bash
python scripts/test_ainative_connection.py
```

### 2.2 Create ZeroDB Project

Create `scripts/setup_zerodb_project.py`:

```python
import asyncio
import httpx
import os

AINATIVE_API_URL = "https://api.ainative.studio/"
AINATIVE_API_TOKEN = "kLPiP0bzgKJ0CnNYVt1wq3qxbs2QgDeF2XwyUnxBEOM"

async def create_project():
    """Create a new ZeroDB project for ZeroCommerce."""
    url = f"{AINATIVE_API_URL}v1/public/projects"
    headers = {
        "Authorization": f"Bearer {AINATIVE_API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "name": "ZeroCommerce",
        "description": "Open source eCommerce API for customized products",
        "tier": "free",
        "database_enabled": True
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        project = response.json()
        project_id = project["id"]
        print(f"✅ Project created successfully!")
        print(f"Project ID: {project_id}")
        print(f"\n⚠️  Add this to your .env file:")
        print(f"ZERODB_PROJECT_ID={project_id}")
        return project
    else:
        print(f"❌ Failed to create project: {response.status_code}")
        print(f"Error: {response.text}")
        return None

if __name__ == "__main__":
    asyncio.run(create_project())
```

Run:

```bash
python scripts/setup_zerodb_project.py
```

**IMPORTANT**: Copy the `ZERODB_PROJECT_ID` to your `.env` file!

---

## Step 3: Create ZeroDB Tables

### 3.1 Table Creation Script

Create `scripts/create_zerodb_tables.py`:

```python
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

AINATIVE_API_URL = os.getenv("AINATIVE_API_URL")
AINATIVE_API_TOKEN = os.getenv("AINATIVE_API_TOKEN")
ZERODB_PROJECT_ID = os.getenv("ZERODB_PROJECT_ID")

async def create_table(table_name: str, schema: dict, indexes: list):
    """Create a ZeroDB table."""
    url = f"{AINATIVE_API_URL}v1/public/zerodb/{ZERODB_PROJECT_ID}/database/tables"
    headers = {
        "Authorization": f"Bearer {AINATIVE_API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "name": table_name,
        "schema": schema,
        "indexes": indexes
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)

    if response.status_code in [200, 201]:
        print(f"✅ Table '{table_name}' created successfully")
        return response.json()
    else:
        print(f"❌ Failed to create table '{table_name}': {response.status_code}")
        print(f"Error: {response.text}")
        return None

async def create_all_tables():
    """Create all required tables for ZeroCommerce."""

    # Products table
    await create_table(
        table_name="products",
        schema={
            "id": "string",
            "name": "string",
            "description": "string",
            "price": "number",
            "template_id": "string",
            "template_data": "object",
            "option_sets": "array",
            "is_active": "boolean",
            "created_at": "string",
            "updated_at": "string",
            "metadata": "object"
        },
        indexes=["id", "template_id", "is_active", "name"]
    )

    # Templates table
    await create_table(
        table_name="templates",
        schema={
            "id": "string",
            "name": "string",
            "description": "string",
            "version": "integer",
            "zones": "array",
            "is_active": "boolean",
            "created_at": "string",
            "updated_at": "string"
        },
        indexes=["id", "name", "is_active"]
    )

    # Orders table
    await create_table(
        table_name="orders",
        schema={
            "id": "string",
            "user_id": "string",
            "user_email": "string",
            "status": "string",
            "total_amount": "number",
            "items": "array",
            "payment_events": "array",
            "shipping_address": "object",
            "billing_address": "object",
            "created_at": "string",
            "updated_at": "string"
        },
        indexes=["id", "user_id", "user_email", "status", "created_at"]
    )

    # Sessions table
    await create_table(
        table_name="sessions",
        schema={
            "id": "string",
            "session_key": "string",
            "product_id": "string",
            "template_id": "string",
            "options": "object",
            "is_active": "boolean",
            "created_at": "string",
            "updated_at": "string"
        },
        indexes=["id", "session_key", "product_id"]
    )

    # Webhook logs table
    await create_table(
        table_name="webhook_logs",
        schema={
            "id": "string",
            "event_type": "string",
            "payload": "object",
            "response_status": "integer",
            "retry_count": "integer",
            "sent_at": "string",
            "created_at": "string"
        },
        indexes=["id", "event_type", "sent_at"]
    )

    print("\n✅ All tables created successfully!")

if __name__ == "__main__":
    asyncio.run(create_all_tables())
```

Run:

```bash
python scripts/create_zerodb_tables.py
```

---

## Step 4: Implement Core Services

### 4.1 ZeroDB Service

Create `app/services/zerodb_service.py`:

```python
"""
ZeroDB service for database operations.
"""
import httpx
from typing import Optional, Dict, List, Any
from app.core.config import settings


class ZeroDBService:
    """Service for interacting with ZeroDB API."""

    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize ZeroDB service.

        Args:
            project_id: ZeroDB project ID (defaults to settings)
        """
        self.project_id = project_id or settings.ZERODB_PROJECT_ID
        self.base_url = f"{settings.AINATIVE_API_URL}v1/public/zerodb/{self.project_id}/database"
        self.headers = {
            "Authorization": f"Bearer {settings.AINATIVE_API_TOKEN}",
            "Content-Type": "application/json"
        }

    async def create_row(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new row in a table.

        Args:
            table: Table name
            data: Row data

        Returns:
            Created row data
        """
        url = f"{self.base_url}/tables/{table}/rows"

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def get_row(self, table: str, row_id: str) -> Dict[str, Any]:
        """
        Get a row by ID.

        Args:
            table: Table name
            row_id: Row ID

        Returns:
            Row data
        """
        url = f"{self.base_url}/tables/{table}/rows/{row_id}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def query_rows(
        self,
        table: str,
        filter: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        skip: int = 0,
        sort: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """
        Query rows with filters.

        Args:
            table: Table name
            filter: MongoDB-style filter (e.g., {"price": {"$gte": 10}})
            limit: Maximum results
            skip: Number of results to skip
            sort: Sort specification (e.g., {"created_at": -1})

        Returns:
            Query results with metadata
        """
        url = f"{self.base_url}/tables/{table}/query"

        payload = {
            "filter": filter or {},
            "limit": limit,
            "skip": skip
        }

        if sort:
            payload["sort"] = sort

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()

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
            data: Updated data

        Returns:
            Updated row data
        """
        url = f"{self.base_url}/tables/{table}/rows/{row_id}"

        async with httpx.AsyncClient() as client:
            response = await client.put(url, json=data, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def delete_row(self, table: str, row_id: str) -> Dict[str, Any]:
        """
        Delete a row.

        Args:
            table: Table name
            row_id: Row ID

        Returns:
            Deletion confirmation
        """
        url = f"{self.base_url}/tables/{table}/rows/{row_id}"

        async with httpx.AsyncClient() as client:
            response = await client.delete(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def list_tables(self) -> List[Dict[str, Any]]:
        """
        List all tables in the project.

        Returns:
            List of table metadata
        """
        url = f"{self.base_url}/tables"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json().get("tables", [])
```

### 4.2 AINative Auth Service

Create `app/services/ainative_auth.py`:

```python
"""
AINative authentication service.
"""
import httpx
from typing import Dict, Optional
from fastapi import HTTPException, status
from app.core.config import settings


class AINativeAuthService:
    """Service for AINative authentication."""

    def __init__(self):
        """Initialize AINative auth service."""
        self.base_url = f"{settings.AINATIVE_API_URL}v1/public/auth"
        self.api_token = settings.AINATIVE_API_TOKEN

    async def register_user(
        self,
        email: str,
        password: str,
        name: str
    ) -> Dict[str, any]:
        """
        Register a new user.

        Args:
            email: User email
            password: User password
            name: User full name

        Returns:
            User data

        Raises:
            HTTPException: If registration fails
        """
        url = f"{self.base_url}/register"
        payload = {
            "email": email,
            "password": password,
            "name": name
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get("detail", "Registration failed")
            )

        return response.json()

    async def login(self, email: str, password: str) -> Dict[str, str]:
        """
        Login user and get access token.

        Args:
            email: User email
            password: User password

        Returns:
            Token response with access_token

        Raises:
            HTTPException: If login fails
        """
        url = f"{self.base_url}/login-json"
        payload = {
            "email": email,
            "password": password
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        return response.json()

    async def get_current_user(self, access_token: str) -> Dict[str, any]:
        """
        Get current user from access token.

        Args:
            access_token: JWT access token

        Returns:
            User data

        Raises:
            HTTPException: If token is invalid
        """
        url = f"{self.base_url}/me"
        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )

        return response.json()

    async def refresh_token(self, refresh_token: str) -> Dict[str, str]:
        """
        Refresh access token.

        Args:
            refresh_token: Refresh token

        Returns:
            New token response

        Raises:
            HTTPException: If refresh fails
        """
        url = f"{self.base_url}/refresh"
        headers = {"Authorization": f"Bearer {refresh_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers)

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        return response.json()
```

---

## Step 5: Update Configuration

### 5.1 Update `app/core/config.py`

Add these settings:

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # AINative Authentication
    AINATIVE_API_URL: str = "https://api.ainative.studio/"
    AINATIVE_API_TOKEN: str
    AINATIVE_USERNAME: Optional[str] = None
    AINATIVE_PASSWORD: Optional[str] = None

    # ZeroDB
    ZERODB_PROJECT_ID: str
```

---

## Step 6: Test the Integration

### 6.1 Test ZeroDB Connection

Create `scripts/test_zerodb.py`:

```python
import asyncio
from app.services.zerodb_service import ZeroDBService

async def test_zerodb():
    """Test ZeroDB operations."""
    zerodb = ZeroDBService()

    # List tables
    print("📋 Listing tables...")
    tables = await zerodb.list_tables()
    print(f"Found {len(tables)} tables:")
    for table in tables:
        print(f"  - {table['name']}")

    # Create a test product
    print("\n📝 Creating test product...")
    product = await zerodb.create_row("products", {
        "id": "test_product_001",
        "name": "Test T-Shirt",
        "description": "A test product",
        "price": 24.99,
        "is_active": True
    })
    print(f"✅ Created product: {product}")

    # Query products
    print("\n🔍 Querying products...")
    results = await zerodb.query_rows(
        "products",
        filter={"is_active": True},
        limit=10
    )
    print(f"Found {len(results.get('results', []))} active products")

    print("\n✅ All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_zerodb())
```

Run:

```bash
python scripts/test_zerodb.py
```

### 6.2 Test Authentication

Create `scripts/test_auth.py`:

```python
import asyncio
from app.services.ainative_auth import AINativeAuthService

async def test_auth():
    """Test AINative authentication."""
    auth = AINativeAuthService()

    # Register a test user
    print("📝 Registering test user...")
    try:
        user = await auth.register_user(
            email="test@zerocommerce.com",
            password="TestPassword123!",
            name="Test User"
        )
        print(f"✅ User registered: {user['email']}")
    except Exception as e:
        print(f"⚠️  Registration failed (user may already exist): {e}")

    # Login
    print("\n🔐 Logging in...")
    tokens = await auth.login(
        email="test@zerocommerce.com",
        password="TestPassword123!"
    )
    access_token = tokens["access_token"]
    print(f"✅ Got access token: {access_token[:50]}...")

    # Get current user
    print("\n👤 Getting current user...")
    current_user = await auth.get_current_user(access_token)
    print(f"✅ Current user: {current_user['email']} (role: {current_user['role']})")

    print("\n✅ All authentication tests passed!")

if __name__ == "__main__":
    asyncio.run(test_auth())
```

Run:

```bash
python scripts/test_auth.py
```

---

## Step 7: Next Steps

After completing the quick start:

1. **Review Gap Analysis**: Read `docs/migration/ZERODB_MIGRATION_GAP_ANALYSIS.md`
2. **Plan Migration**: Choose between full migration or hybrid approach
3. **Update Endpoints**: Gradually migrate API endpoints to use ZeroDBService
4. **Add Authentication**: Replace API key auth with AINative OAuth
5. **Test Thoroughly**: Run comprehensive tests before production deployment

---

## Troubleshooting

### Common Issues

**1. "Invalid API token" error**
- Verify `AINATIVE_API_TOKEN` is correct in `.env`
- Check token hasn't expired
- Ensure no extra spaces in `.env` file

**2. "Project not found" error**
- Verify `ZERODB_PROJECT_ID` is set correctly
- Run `scripts/setup_zerodb_project.py` to create project

**3. "Table already exists" error**
- Tables can only be created once
- Use `GET /tables` to list existing tables
- Delete and recreate if needed (data will be lost)

**4. Import errors**
- Run `pip install -r requirements.txt`
- Ensure virtual environment is activated

---

## Support

For issues or questions:
- Review the full gap analysis document
- Check AINative API documentation
- Contact: support@ainative.studio

---

**Quick Start Complete!** 🎉

You now have ZeroDB and AINative authentication configured. Proceed with the migration plan outlined in the gap analysis document.
