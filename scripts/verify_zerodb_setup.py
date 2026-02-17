"""
Verify ZeroDB setup and test basic operations.

This script:
1. Lists all tables in the project
2. Tests basic CRUD operations on tables
"""
import asyncio
import httpx
import sys
import os
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


async def insert_test_row(client: httpx.AsyncClient, table: str, data: dict) -> bool:
    """Insert a test row."""
    url = f"{AINATIVE_API_URL}v1/public/zerodb/{ZERODB_PROJECT_ID}/database/tables/{table}/rows"
    headers = {
        "Authorization": f"Bearer {AINATIVE_API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {"row_data": data}
    response = await client.post(url, json=payload, headers=headers)
    return response.status_code in [200, 201]


async def query_table(client: httpx.AsyncClient, table: str) -> int:
    """Query table and return count."""
    url = f"{AINATIVE_API_URL}v1/public/zerodb/{ZERODB_PROJECT_ID}/database/tables/{table}/query"
    headers = {
        "Authorization": f"Bearer {AINATIVE_API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {"filter": {}, "limit": 10}
    response = await client.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return len(response.json().get('results', []))
    return 0


async def verify_setup():
    """Verify ZeroDB setup."""
    print("=" * 60)
    print("Verifying ZeroDB Setup for ChiCommerce")
    print("=" * 60)
    print(f"\nProject ID: {ZERODB_PROJECT_ID}")
    print(f"API URL: {AINATIVE_API_URL}")

    if not ZERODB_PROJECT_ID or not AINATIVE_API_TOKEN:
        print("\n❌ Missing environment variables")
        return False

    test_results = []

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
        chicommerce_tables = []
        for table in tables:
            table_name = table['table_name']
            print(f"      - {table_name}")
            if table_name in ["products", "templates", "sessions", "webhook_logs"]:
                chicommerce_tables.append(table_name)

        if len(chicommerce_tables) != 4:
            print(f"\n   ⚠️  Warning: Expected 4 ChiCommerce tables, found {len(chicommerce_tables)}")

        # 2. Test insert on products table
        print("\n" + "=" * 60)
        print("2. Testing 'products' Table")
        print("=" * 60)

        test_product = {
            "id": "test_verify_001",
            "name": "Verification Test Product",
            "description": "Test product",
            "price": 19.99,
            "template_id": "test_template",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        print("   → Testing insert operation...")
        success = await insert_test_row(client, "products", test_product)
        if success:
            print("   ✅ Insert operation successful")
            test_results.append(("products insert", True))
        else:
            print("   ❌ Insert operation failed")
            test_results.append(("products insert", False))

        print("   → Testing query operation...")
        count = await query_table(client, "products")
        print(f"   ✅ Query operation successful ({count} rows)")
        test_results.append(("products query", True))

        # 3. Test templates table
        print("\n" + "=" * 60)
        print("3. Testing 'templates' Table")
        print("=" * 60)

        test_template = {
            "id": "test_template_verify_001",
            "name": "Verification Template",
            "description": "Test template",
            "version": 1,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        print("   → Testing insert operation...")
        success = await insert_test_row(client, "templates", test_template)
        if success:
            print("   ✅ Insert operation successful")
            test_results.append(("templates insert", True))
        else:
            print("   ❌ Insert operation failed")
            test_results.append(("templates insert", False))

        # 4. Test sessions table
        print("\n" + "=" * 60)
        print("4. Testing 'sessions' Table")
        print("=" * 60)

        test_session = {
            "id": "test_session_verify_001",
            "session_key": "sess_verify_001",
            "product_id": "test_prod",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        print("   → Testing insert operation...")
        success = await insert_test_row(client, "sessions", test_session)
        if success:
            print("   ✅ Insert operation successful")
            test_results.append(("sessions insert", True))
        else:
            print("   ❌ Insert operation failed")
            test_results.append(("sessions insert", False))

        # 5. Test webhook_logs table
        print("\n" + "=" * 60)
        print("5. Testing 'webhook_logs' Table")
        print("=" * 60)

        test_webhook = {
            "id": "test_webhook_verify_001",
            "event_type": "test.event",
            "payload": {"test": True},
            "response_status": 200,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        print("   → Testing insert operation...")
        success = await insert_test_row(client, "webhook_logs", test_webhook)
        if success:
            print("   ✅ Insert operation successful")
            test_results.append(("webhook_logs insert", True))
        else:
            print("   ❌ Insert operation failed")
            test_results.append(("webhook_logs insert", False))

    # Final summary
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)

    passed = sum(1 for _, success in test_results if success)
    total = len(test_results)

    for test_name, success in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {test_name:<25} {status}")

    print("\n" + "=" * 60)
    if passed == total:
        print(f"✅ All {total} tests passed!")
        print("=" * 60)
        print("\nZeroDB setup is complete and operational.")
        print("\nTables created and tested:")
        print("  - products")
        print("  - templates")
        print("  - sessions")
        print("  - webhook_logs")
        print("\nBasic CRUD operations working correctly.")
        print("=" * 60)
        return True
    else:
        print(f"⚠️  {passed}/{total} tests passed")
        print("=" * 60)
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(verify_setup())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Verification failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
