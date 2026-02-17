"""
Create all required ZeroDB tables for ChiCommerce.

This script creates the following tables:
- products: Product catalog with template data
- templates: Customization templates
- customization_sessions: Customization sessions with crypto-secure keys
- webhook_logs: Webhook event logs
"""
import asyncio
import httpx
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

AINATIVE_API_URL = os.getenv("AINATIVE_API_URL", "https://api.ainative.studio/")
AINATIVE_API_TOKEN = os.getenv("AINATIVE_API_TOKEN")
ZERODB_PROJECT_ID = os.getenv("ZERODB_PROJECT_ID")


async def create_table(client: httpx.AsyncClient, table_name: str, schema: dict, indexes: list) -> bool:
    """
    Create a ZeroDB table.

    Args:
        client: HTTP client instance
        table_name: Name of the table to create
        schema: Schema definition
        indexes: List of fields to index

    Returns:
        True if successful, False otherwise
    """
    url = f"{AINATIVE_API_URL}v1/public/zerodb/{ZERODB_PROJECT_ID}/database/tables"
    headers = {
        "Authorization": f"Bearer {AINATIVE_API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "table_name": table_name,
        "schema": schema,
        "indexes": indexes
    }

    try:
        response = await client.post(url, json=payload, headers=headers)

        if response.status_code in [200, 201]:
            print(f"   ✅ Table '{table_name}' created successfully")
            return True
        else:
            print(f"   ❌ Failed to create table '{table_name}': {response.status_code}")
            print(f"      Error: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Exception creating table '{table_name}': {str(e)}")
        return False


async def create_all_tables():
    """Create all required tables for ChiCommerce."""
    print("=" * 60)
    print("Creating ZeroDB Tables for ChiCommerce")
    print("=" * 60)
    print(f"\nProject ID: {ZERODB_PROJECT_ID}")
    print(f"API URL: {AINATIVE_API_URL}")
    print("\n" + "=" * 60)

    if not ZERODB_PROJECT_ID:
        print("❌ ZERODB_PROJECT_ID not set in .env file")
        return False

    if not AINATIVE_API_TOKEN:
        print("❌ AINATIVE_API_TOKEN not set in .env file")
        return False

    results = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Products table
        print("\n1. Creating 'products' table...")
        result = await create_table(
            client,
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
        results.append(("products", result))

        # 2. Templates table
        print("\n2. Creating 'templates' table...")
        result = await create_table(
            client,
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
        results.append(("templates", result))

        # 3. Customization Sessions table
        print("\n3. Creating 'customization_sessions' table...")
        result = await create_table(
            client,
            table_name="customization_sessions",
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
            indexes=["id", "session_key", "product_id", "is_active", "created_at"]
        )
        results.append(("customization_sessions", result))

        # 4. Webhook logs table
        print("\n4. Creating 'webhook_logs' table...")
        result = await create_table(
            client,
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
        results.append(("webhook_logs", result))

    # Summary
    print("\n" + "=" * 60)
    print("Table Creation Summary")
    print("=" * 60)

    success_count = sum(1 for _, success in results if success)
    total_count = len(results)

    for table_name, success in results:
        status = "✅ Created" if success else "❌ Failed"
        print(f"  {table_name:<20} {status}")

    print("\n" + "=" * 60)
    if success_count == total_count:
        print(f"✅ All {total_count} tables created successfully!")
        print("=" * 60)
        return True
    else:
        print(f"⚠️  {success_count}/{total_count} tables created successfully")
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = asyncio.run(create_all_tables())
    sys.exit(0 if success else 1)
