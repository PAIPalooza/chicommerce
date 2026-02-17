"""
Create ZeroDB project for ChiCommerce.

This script creates a new ZeroDB project via the AINative API
and outputs the project ID for configuration.
"""
import asyncio
import httpx
import sys
import json

AINATIVE_API_URL = "https://api.ainative.studio/"
AINATIVE_API_TOKEN = "kLPiP0bzgKJ0CnNYVt1wq3qxbs2QgDeF2XwyUnxBEOM"


async def create_project():
    """Create a new ZeroDB project for ChiCommerce."""
    print("=" * 60)
    print("Creating ZeroDB Project for ChiCommerce")
    print("=" * 60)

    url = f"{AINATIVE_API_URL}v1/public/projects"
    headers = {
        "Authorization": f"Bearer {AINATIVE_API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "name": "ChiCommerce",
        "description": "Open source eCommerce API for customized products",
        "tier": "free",
        "database_enabled": True
    }

    print(f"\n📝 Creating project with configuration:")
    print(f"   Name: {payload['name']}")
    print(f"   Description: {payload['description']}")
    print(f"   Tier: {payload['tier']}")
    print(f"   Database: {payload['database_enabled']}")
    print("\n⏳ Sending request to AINative API...")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)

        if response.status_code == 201:
            project = response.json()
            project_id = project["id"]
            print("\n" + "=" * 60)
            print("✅ Project created successfully!")
            print("=" * 60)
            print(f"\n📊 Project Details:")
            print(f"   ID: {project_id}")
            print(f"   Name: {project.get('name')}")
            print(f"   Status: {project.get('status')}")
            print(f"   Tier: {project.get('tier')}")
            print(f"   Database Enabled: {project.get('database_enabled')}")

            print("\n" + "=" * 60)
            print("⚠️  IMPORTANT: Add this to your .env file:")
            print("=" * 60)
            print(f"ZERODB_PROJECT_ID={project_id}")
            print("=" * 60)

            return project_id
        else:
            print(f"\n❌ Failed to create project: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except httpx.TimeoutException:
        print("\n❌ Request timeout - API may be unreachable")
        return None
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    project_id = asyncio.run(create_project())
    sys.exit(0 if project_id else 1)
