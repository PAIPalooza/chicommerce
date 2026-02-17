"""
Verify ZeroDB setup and test basic operations.

This script:
1. Lists all tables in the project
2. Tests insert operations on each table
3. Tests query operations
4. Tests update operations
5. Tests delete operations
"""
import asyncio
import httpx
import sys
import os
import json
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

AINATIVE_API_URL = os.getenv("AINATIVE_API_URL", "https://api.ainative.studio/")
AINATIVE_API_TOKEN = os.getenv("AINATIVE_API_TOKEN")
ZERODB_PROJECT_ID = os.getenv("ZERODB_PROJECT_ID")


async def list_tables(client: httpx.AsyncClient) -> dict:
    """List all tables in the project."""
    url = f"{AINATIVE_API_URL}v1/public/zerodb/{ZERODB_PROJECT_ID}/database/tables"
    headers = {"Authorization": f"Bearer {AINATIVE_API_TOKEN}"}

    response = await client.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"   ❌ Failed to list tables: {response.status_code}")
        return {}


async def insert_row(client: httpx.AsyncClient, table: str, data: dict) -> dict:
    """Insert a row into a table."""
    url = f"{AINATIVE_API_URL}v1/public/zerodb/{ZERODB_PROJECT_ID}/database/tables/{table}/rows"
    headers = {
        "Authorization": f"Bearer {AINATIVE_API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {"row_data": data}
    response = await client.post(url, json=payload, headers=headers)
    if response.status_code in [200, 201]:
        return response.json()
    else:
        raise Exception(f"Insert failed: {response.status_code} - {response.text}")


async def query_rows(client: httpx.AsyncClient, table: str, filter_data: dict = None) -> dict:
    """Query rows from a table."""
    url = f"{AINATIVE_API_URL}v1/public/zerodb/{ZERODB_PROJECT_ID}/database/tables/{table}/query"
    headers = {
        "Authorization": f"Bearer {AINATIVE_API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "filter": filter_data or {},
        "limit": 10
    }

    response = await client.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Query failed: {response.status_code} - {response.text}")


async def get_row(client: httpx.AsyncClient, table: str, row_id: str) -> dict:
    """Get a specific row by ID."""
    url = f"{AINATIVE_API_URL}v1/public/zerodb/{ZERODB_PROJECT_ID}/database/tables/{table}/rows/{row_id}"
    headers = {"Authorization": f"Bearer {AINATIVE_API_TOKEN}"}

    response = await client.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Get row failed: {response.status_code} - {response.text}")


async def update_row(client: httpx.AsyncClient, table: str, row_id: str, data: dict) -> dict:
    """Update a row."""
    url = f"{AINATIVE_API_URL}v1/public/zerodb/{ZERODB_PROJECT_ID}/database/tables/{table}/rows/{row_id}"
    headers = {
        "Authorization": f"Bearer {AINATIVE_API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {"row_data": data}
    response = await client.put(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Update failed: {response.status_code} - {response.text}")


async def delete_row(client: httpx.AsyncClient, table: str, row_id: str) -> dict:
    """Delete a row."""
    url = f"{AINATIVE_API_URL}v1/public/zerodb/{ZERODB_PROJECT_ID}/database/tables/{table}/rows/{row_id}"
    headers = {"Authorization": f"Bearer {AINATIVE_API_TOKEN}"}

    response = await client.delete(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Delete failed: {response.status_code} - {response.text}")


async def verify_setup():
    """Verify ZeroDB setup with comprehensive tests."""
    print("=" * 60)
    print("Verifying ZeroDB Setup for ChiCommerce")
    print("=" * 60)
    print(f"\nProject ID: {ZERODB_PROJECT_ID}")
    print(f"API URL: {AINATIVE_API_URL}")

    if not ZERODB_PROJECT_ID or not AINATIVE_API_TOKEN:
        print("\n❌ Missing environment variables")
        return False

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. List tables
        print("\n" + "=" * 60)
        print("1. Listing Tables")
        print("=" * 60)
        tables_response = await list_tables(client)
        tables = tables_response.get("data", [])

        if not tables:
            print("   ❌ No tables found")
            return False

        print(f"   ✅ Found {len(tables)} tables:")
        for table in tables:
            print(f"      - {table['table_name']} (ID: {table['table_id'][:8]}...)")

        # 2. Test products table
        print("\n" + "=" * 60)
        print("2. Testing 'products' Table")
        print("=" * 60)

        test_product = {
            "id": "test_prod_001",
            "name": "Test T-Shirt",
            "description": "A test product for verification",
            "price": 24.99,
            "template_id": "test_template_001",
            "template_data": {"zones": []},
            "option_sets": [],
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {"test": True}
        }

        print("   → Inserting test product...")
        product = await insert_row(client, "products", test_product)
        print(f"   ✅ Product inserted: {product.get('id')}")

        print("   → Querying products...")
        query_result = await query_rows(client, "products", {"is_active": True})
        print(f"   ✅ Query returned {len(query_result.get('results', []))} products")

        print("   → Getting specific product...")
        fetched_product = await get_row(client, "products", test_product["id"])
        print(f"   ✅ Product retrieved: {fetched_product.get('name')}")

        print("   → Updating product...")
        updated_data = test_product.copy()
        updated_data["price"] = 29.99
        updated_product = await update_row(client, "products", test_product["id"], updated_data)
        print(f"   ✅ Product updated: price = ${updated_product.get('price')}")

        print("   → Deleting product...")
        await delete_row(client, "products", test_product["id"])
        print(f"   ✅ Product deleted")

        # 3. Test templates table
        print("\n" + "=" * 60)
        print("3. Testing 'templates' Table")
        print("=" * 60)

        test_template = {
            "id": "test_template_001",
            "name": "Test Template",
            "description": "A test template for verification",
            "version": 1,
            "zones": [{"name": "Front", "type": "image"}],
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        print("   → Inserting test template...")
        template = await insert_row(client, "templates", test_template)
        print(f"   ✅ Template inserted: {template.get('id')}")

        print("   → Querying templates...")
        query_result = await query_rows(client, "templates")
        print(f"   ✅ Query returned {len(query_result.get('results', []))} templates")

        print("   → Deleting template...")
        await delete_row(client, "templates", test_template["id"])
        print(f"   ✅ Template deleted")

        # 4. Test sessions table
        print("\n" + "=" * 60)
        print("4. Testing 'sessions' Table")
        print("=" * 60)

        test_session = {
            "id": "test_session_001",
            "session_key": "sess_test_001",
            "product_id": "test_prod_001",
            "template_id": "test_template_001",
            "options": {"color": "blue", "size": "M"},
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        print("   → Inserting test session...")
        session = await insert_row(client, "sessions", test_session)
        print(f"   ✅ Session inserted: {session.get('id')}")

        print("   → Querying sessions...")
        query_result = await query_rows(client, "sessions", {"is_active": True})
        print(f"   ✅ Query returned {len(query_result.get('results', []))} sessions")

        print("   → Deleting session...")
        await delete_row(client, "sessions", test_session["id"])
        print(f"   ✅ Session deleted")

        # 5. Test webhook_logs table
        print("\n" + "=" * 60)
        print("5. Testing 'webhook_logs' Table")
        print("=" * 60)

        test_webhook = {
            "id": "test_webhook_001",
            "event_type": "order.created",
            "payload": {"order_id": "ord_001", "total": 99.99},
            "response_status": 200,
            "retry_count": 0,
            "sent_at": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat()
        }

        print("   → Inserting test webhook log...")
        webhook = await insert_row(client, "webhook_logs", test_webhook)
        print(f"   ✅ Webhook log inserted: {webhook.get('id')}")

        print("   → Querying webhook logs...")
        query_result = await query_rows(client, "webhook_logs")
        print(f"   ✅ Query returned {len(query_result.get('results', []))} webhook logs")

        print("   → Deleting webhook log...")
        await delete_row(client, "webhook_logs", test_webhook["id"])
        print(f"   ✅ Webhook log deleted")

    # Final summary
    print("\n" + "=" * 60)
    print("✅ All Verification Tests Passed!")
    print("=" * 60)
    print("\nZeroDB setup is complete and operational.")
    print("\nTables created and tested:")
    print("  - products")
    print("  - templates")
    print("  - sessions")
    print("  - webhook_logs")
    print("\nAll CRUD operations (Create, Read, Update, Delete) working correctly.")
    print("=" * 60)

    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(verify_setup())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Verification failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
